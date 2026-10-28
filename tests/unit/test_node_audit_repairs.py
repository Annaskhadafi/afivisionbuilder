import sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'engine'))
from custom_model_runtime import _run_roboflow_universe
from cloud_sinks import upload_to_s3, dispatch_notification
from mqtt_gateway import MqttPublisherClient, process_mqtt_publisher
from workflow_export import _determine_needed_engine_files, _determine_required_packages

def test_audit_fixes():
    frame = np.zeros((40, 40, 3), dtype=np.uint8)
    try:
        _run_roboflow_universe(frame, 'model/1', '', .5, 'n', 'detector', {})
        assert False
    except ValueError:
        pass
    with patch('mqtt_gateway.PAHO_AVAILABLE', False):
        assert MqttPublisherClient('localhost', 1883).publish('t', '{}') is False
    with patch.object(MqttPublisherClient, 'get_client') as client:
        import json
        client.return_value.publish.return_value = True
        client.return_value.connected = True
        process_mqtt_publisher({'config': {'publishMode': 'always'}}, [{'class':'person','score':.9,'trackId':4}], {}, 100)
        det = json.loads(client.return_value.publish.call_args.args[1])['detections'][0]
        assert (det['confidence'], det['track_id']) == (.9, 4)
    assert upload_to_s3(frame, None, {}, {}, False)['status'] != 'uploaded'
    assert dispatch_notification({}, None, {'channel':'whatsapp', 'destinationId':'test'}, {}, False)['status'] == 'unsupported_channel'
    graph = {'nodes': [{'type': t} for t in ('camera_focus','ocr_reader','screenshot_capture','telegram_notification','mqtt_publisher')]}
    assert {'classical_cv.py','ocr_engine.py','screenshot_capture.py','telegram_sink.py'} <= _determine_needed_engine_files(graph)
    assert 'paho-mqtt' in _determine_required_packages(graph)

def test_separate_tracked_workers_and_vehicles():
    from lpr_license_plate import process_license_plates
    from ppe_compliance import PPEComplianceMatrix
    vehicles = [{'class':'car','trackId':1,'bbox':[0,0,10,10],'plate_text':'B 1234 ABC'}, {'class':'car','trackId':2,'bbox':[20,0,10,10],'plate_text':'B 5678 XYZ'}]
    out, _ = process_license_plates(None, vehicles, {'temporalVotingFrames':1}, {}, 100)
    assert out[0]['plateNumber'] != out[1]['plateNumber']
    workers = [{'class':'person','trackId':i,'bbox':[i*30,0,20,80]} for i in (1,2)]
    _, events = PPEComplianceMatrix('test', {}).evaluate(workers, 100)
    assert len(events) == 2
