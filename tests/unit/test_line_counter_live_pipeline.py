import time
from threading import Event
from unittest.mock import patch
import numpy as np
from engine import core


def test_video_counter_waits_for_tracker_and_preserves_frames():
    tracker_started, tracker_continue = Event(), Event()
    reads, rendered = [], []
    class Source:
        is_static = False
        is_exhausted = False
        fps = 30
        def __init__(self, *_): self.pos = 0
        def open(self): return 'local recording', 120, 100
        def read(self):
            if self.pos == 10:
                self.is_exhausted = True
                return False, None
            self.pos += 1
            reads.append(self.pos)
            frame = np.zeros((100, 120, 3), np.uint8)
            frame[0, 0, 0] = self.pos
            return True, frame
        def release(self): pass
    original_tracker = core.engine.ObjectTracker
    class SlowTracker(original_tracker):
        def update(self, *args, **kwargs):
            if not tracker_started.is_set():
                tracker_started.set()
                assert tracker_continue.wait(5)
            return super().update(*args, **kwargs)
    def infer(batch, _node):
        return [[{'kind':'detection','sourceNodeId':'det','class':'person','score':0.9,
                  'bbox':[12 + int(f[0,0,0]) * 6, 30, 30, 40]}] for f in batch]
    draw = core.engine.draw_detections
    def draw_spy(frame, detections, *args, **kwargs):
        rendered.extend(dict(d) for d in detections)
        return draw(frame, detections, *args, **kwargs)
    workflow={'nodes':[
        {'id':'input','type':'input','config':{'sourceType':'video','filePath':'fake.mp4','loop':False,'dropFrames':True}},
        {'id':'det','type':'detector','config':{'engine':'rfdetr'}},
        {'id':'track_17','type':'tracker','config':{'algorithm':'cbiou','enableReid':False}},
        {'id':'line','type':'line_counter','config':{'startPoint':'60,10','endPoint':'60,90','triggerAnchor':'center','hysteresisDistance':2,'reArmCooldown':0}},
        {'id':'preview','type':'preview','config':{'showLabels':True,'showTrails':True}},
    ], 'edges':[['input','det'],['det','track_17'],['track_17','line'],['line','preview']]}
    runner = core.WorkflowRunner(on_frame=lambda *_: None, native_preview=False)
    with patch.object(core.engine,'OpenCVInputSource',Source), patch.object(core.engine,'load_rfdetr_model',return_value=object()), patch.object(core.engine,'run_rfdetr_batch',side_effect=infer), patch.object(core.engine,'ObjectTracker',SlowTracker), patch.object(core.engine,'draw_detections',side_effect=draw_spy):
        runner.start(workflow)
        try:
            assert tracker_started.wait(8)
            time.sleep(0.15)
            assert reads == [1]
            assert runner.status()["state"] == "starting"
            tracker_continue.set()
            runner._thread.join(15)
            assert not runner._thread.is_alive()
            assert runner.status()['error'] is None
            assert reads == list(range(1,11))
            assert any(d.get('trackId') is not None and d.get('trail') for d in rendered)
            assert runner._event_runtime['line']['total_in'] + runner._event_runtime['line']['total_out'] == 1
            assert runner.status()['nodeTelemetry']['preview']['itemCount'] > 0
        finally:
            tracker_continue.set()
            runner.stop()


def test_preview_shows_detection_before_tracker_confirms_id():
    from engine import main
    workflow = {'nodes': [
        {'id':'input','type':'input','config':{}}, {'id':'det','type':'detector','config':{}},
        {'id':'trk','type':'tracker','config':{}}, {'id':'line','type':'line_counter','config':{}},
        {'id':'preview','type':'preview','config':{}}],
        'edges': [['input','det'],['det','trk'],['trk','line'],['line','preview']]}
    detection = {'kind':'detection','sourceNodeId':'det','class':'person','bbox':[1,2,10,20]}
    assert main.detections_for_node(workflow, 'preview', [detection], [detection], []) == [detection]
