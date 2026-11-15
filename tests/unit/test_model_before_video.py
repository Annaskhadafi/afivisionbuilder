from threading import Event, Thread
from unittest.mock import patch
import numpy as np
import pytest
from engine import core


@pytest.mark.parametrize('threaded', [True, False])
def test_source_waits_for_model_and_first_inference(threaded):
    loading, load_ready, infer_started, infer_ready = Event(), Event(), Event(), Event()
    opened = Event()
    reads = []
    class Source:
        is_static = False
        is_exhausted = False
        fps = 30
        def __init__(self, *_): pass
        def open(self):
            opened.set()
            return 'fake video', 32, 24
        def read(self):
            reads.append(len(reads))
            if len(reads) > 2:
                self.is_exhausted = True
                return False, None
            return True, np.zeros((24, 32, 3), dtype=np.uint8)
        def release(self): pass
    def load(*args, **kwargs):
        loading.set()
        assert load_ready.wait(5)
        return object()
    def infer(*args, **kwargs):
        infer_started.set()
        assert infer_ready.wait(5)
        return [[]] if threaded else []
    workflow = {'nodes': [
        {'id':'input','type':'input','config':{'sourceType':'video','filePath':'fake','loop':False,'dropFrames':False}},
        {'id':'det','type':'detector','config':{'engine':'rfdetr'}},
        {'id':'preview','type':'preview','config':{}}
    ], 'edges':[['input','det'],['det','preview']]}
    runner = core.WorkflowRunner(on_frame=lambda *_: None, native_preview=False)
    runner._python_context = {}
    target = runner._run_pipeline if threaded else runner._run_serial
    with patch.object(core.engine, 'OpenCVInputSource', Source), patch.object(core.engine, 'load_rfdetr_model', side_effect=load), patch.object(core.engine, 'run_rfdetr_batch', side_effect=infer), patch.object(core.engine, 'run_rfdetr_frame', side_effect=infer):
        if threaded:
            runner.start(workflow)
            worker = runner._thread
        else:
            worker = Thread(target=target, args=(workflow,))
            worker.start()
        try:
            assert loading.wait(5)
            assert not opened.is_set()
            load_ready.set()
            assert infer_started.wait(5)
            assert opened.is_set()
            assert len(reads) == 1
            infer_ready.set()
            worker.join(8)
            assert not worker.is_alive()
            assert runner.status()['error'] is None
            assert len(reads) >= 2
        finally:
            load_ready.set()
            infer_ready.set()
            runner._stop_event.set()
            worker.join(8)
