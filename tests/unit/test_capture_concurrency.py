import cv2
from engine import main


def test_capture_operations_wait_for_inflight_read():
    from threading import Event, Thread

    entered, resume, seek_finished = Event(), Event(), Event()
    class Capture:
        def read(self):
            entered.set()
            assert resume.wait(3)
            return False, None
        def set(self, *_args):
            return True
        def release(self):
            pass
    source = main.OpenCVInputSource(cv2, {"loop": False, "streamUrl": "test", "autoReconnect": False})
    source.capture = Capture()
    source._finite_video = True
    reader = Thread(target=source.read)
    seeker = Thread(target=lambda: (source.seek_to_frame(4), seek_finished.set()))
    reader.start()
    assert entered.wait(2)
    seeker.start()
    assert not seek_finished.wait(0.1)
    resume.set()
    reader.join(2)
    seeker.join(2)
    assert seek_finished.is_set()
    source.release()
    assert source.capture is None
