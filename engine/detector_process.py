"""Optional TensorRT process isolation with bounded, ordered shared-memory input."""
from __future__ import annotations

import multiprocessing as mp
from multiprocessing import spawn
from multiprocessing.shared_memory import SharedMemory
import os
import sys
from threading import Lock
import time
import traceback


_process_start_lock = Lock()


def _start_process(process):
    # Windows' normal multiprocessing launcher uses console creation flags of
    # zero. pythonw avoids flashing a console beside the GUI. Restore the global
    # multiprocessing executable immediately after this child's startup.
    with _process_start_lock:
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if os.name != "nt" or not os.path.isfile(pythonw):
            process.start()
            return
        previous = spawn.get_executable()
        try:
            mp.set_executable(pythonw)
            process.start()
        finally:
            mp.set_executable(previous)


class DetectorProcessStopped(InterruptedError):
    """The workflow stopped while waiting for its detector process."""


def _detector_worker(connection, config):
    """Module-level spawn target; the desktop AI interpreter is source-only."""
    storage = None
    try:
        # Keep native TensorRT diagnostics off the AI worker's JSON stdout pipe.
        if sys.stderr is not None:
            try:
                os.dup2(sys.stderr.fileno(), 1)
            except (AttributeError, OSError, ValueError):
                pass
        import numpy as np
        import main as engine

        runtime = engine.load_rfdetr_tensorrt(config)
        connection.send({"ok": True, "value": {"input_shape": tuple(runtime.input_shape)}})
        while True:
            request = connection.recv()
            if request["operation"] == "close":
                return
            try:
                if request["operation"] != "infer":
                    raise ValueError("Unsupported detector process operation")
                if storage is None or storage.name != request["storage"]:
                    if storage is not None:
                        storage.close()
                    storage = SharedMemory(name=request["storage"])
                frames = [np.ndarray(tuple(item["shape"]), dtype=np.dtype(item["dtype"]),
                                     buffer=storage.buf, offset=item["offset"])
                          for item in request["frames"]]
                try:
                    value = engine.run_rfdetr_tensorrt_batch(frames, request["node"])
                finally:
                    del frames
                connection.send({"ok": True, "value": value})
            except Exception:
                connection.send({"ok": False, "error": traceback.format_exc()})
    except (EOFError, BrokenPipeError):
        pass
    except BaseException:
        try:
            connection.send({"ok": False, "error": traceback.format_exc()})
        except (EOFError, BrokenPipeError, OSError):
            pass
    finally:
        if storage is not None:
            storage.close()
        connection.close()


class TensorRTDetectorProcess:
    """One run-owned model process; synchronous replies retain frame ordering.

    At most 128 MiB of input pixels are staged. Larger workflow batches are split
    into ordered requests instead of allocating unbounded shared memory. Only
    completed requests allow a slot to be reused. Stop checks interrupt waits,
    including model loading, without waiting for the inference timeout.
    """

    def __init__(self, config, stop_event=None, *, timeout=300,
                 max_shared_bytes=128 * 1024 * 1024, _worker_target=None):
        self.stop_event = stop_event
        self.timeout = float(timeout)
        self.max_shared_bytes = max(1, int(max_shared_bytes))
        self._lock = Lock()
        self._storage = None
        self._closed = False
        context = mp.get_context("spawn")
        self._connection, child_connection = context.Pipe()
        self._process = context.Process(target=_worker_target or _detector_worker,
            args=(child_connection, dict(config)), name="visonode-tensorrt", daemon=True)
        try:
            _start_process(self._process)
        except BaseException:
            child_connection.close()
            self._connection.close()
            raise
        child_connection.close()
        try:
            self.input_shape = tuple(self._receive()["input_shape"])
        except BaseException:
            self.close()
            raise

    def _check_stopped(self):
        if self._closed or (self.stop_event is not None and self.stop_event.is_set()):
            raise DetectorProcessStopped("TensorRT detector process stopped")

    def _receive(self):
        deadline = time.monotonic() + self.timeout
        while True:
            self._check_stopped()
            if self._connection.poll(0.05):
                try:
                    response = self._connection.recv()
                except (EOFError, OSError) as exc:
                    raise RuntimeError("TensorRT detector process disconnected") from exc
                if not response.get("ok"):
                    raise RuntimeError("TensorRT detector process failed:\n" + response.get("error", "unknown error"))
                return response["value"]
            if not self._process.is_alive():
                raise RuntimeError(f"TensorRT detector process exited with code {self._process.exitcode}")
            if time.monotonic() >= deadline:
                # An overdue request still owns its shared pixels and may send
                # a late response. Never allow another request to reuse either.
                self.close()
                raise TimeoutError("TensorRT detector process timed out")

    def run_batch(self, frames, node):
        if not frames:
            return []
        with self._lock:
            self._check_stopped()
            results, pending, size = [], [], 0
            for frame in frames:
                if frame.nbytes > self.max_shared_bytes:
                    raise ValueError(f"Frame exceeds the {self.max_shared_bytes} byte detector staging limit")
                if pending and size + frame.nbytes > self.max_shared_bytes:
                    results.extend(self._run_chunk(pending, node))
                    pending, size = [], 0
                pending.append(frame)
                size += frame.nbytes
            if pending:
                results.extend(self._run_chunk(pending, node))
            return results

    def _run_chunk(self, frames, node):
        import numpy as np

        self._check_stopped()
        total = sum(frame.nbytes for frame in frames)
        if self._storage is None or self._storage.size < total:
            if self._storage is not None:
                self._storage.close()
                self._storage.unlink()
            self._storage = SharedMemory(create=True, size=total)
        metadata, offset = [], 0
        for frame in frames:
            if frame.dtype.hasobject:
                raise ValueError("Detector frames must use a numeric pixel dtype")
            destination = np.ndarray(frame.shape, dtype=frame.dtype, buffer=self._storage.buf, offset=offset)
            np.copyto(destination, frame)
            metadata.append({"shape": tuple(frame.shape), "dtype": frame.dtype.str, "offset": offset})
            offset += frame.nbytes
        del destination
        self._connection.send({"operation": "infer", "storage": self._storage.name,
                               "frames": metadata, "node": node})
        result = self._receive()
        if len(result) != len(frames):
            raise RuntimeError("TensorRT detector process returned an incomplete frame batch")
        return result

    def close(self):
        """Called by the owning run after inference stops; safe to repeat."""
        if self._closed:
            return
        self._closed = True
        try:
            if self._process.is_alive():
                try:
                    self._connection.send({"operation": "close"})
                except (EOFError, BrokenPipeError, OSError):
                    pass
                self._process.join(timeout=0.5)
                if self._process.is_alive():
                    self._process.terminate()
                    self._process.join(timeout=1)
                if self._process.is_alive():
                    self._process.kill()
                    self._process.join(timeout=1)
        finally:
            self._connection.close()
            if self._storage is not None:
                self._storage.close()
                self._storage.unlink()
                self._storage = None
