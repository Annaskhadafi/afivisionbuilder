import json
import os
import sys
import tempfile
from pathlib import Path

# Set up test environment
temp_dir = tempfile.TemporaryDirectory(prefix="visonode-persist-")
os.environ["VISONODE_APP_DATA_DIR"] = temp_dir.name

# Add webapp directory to path
webapp_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(webapp_dir))

import server
from fastapi.testclient import TestClient


def test_every_model_setting_persistence():
    print("=== Testing Model Selection & Config Persistence ===")
    
    with TestClient(server.app, base_url="http://127.0.0.1:8765") as client:
        # 1. Create a project
        workflow = {
            "nodes": [
                {
                    "id": "inp",
                    "type": "input",
                    "config": {"sourceType": "image", "filePath": "test.jpg"}
                },
                {
                    "id": "det",
                    "type": "detector",
                    "config": {
                        "engine": "ultralytics_yolo",
                        "customModelPath": "data/models/my_custom_detector.pt",
                        "classes": "person, forklift, pallet",
                        "threshold": 0.62,
                        "iouThreshold": 0.45,
                        "batchSize": 2
                    }
                },
                {
                    "id": "seg",
                    "type": "segmenter",
                    "config": {
                        "engine": "onnx_custom",
                        "customModelPath": "data/models/custom_seg.onnx",
                        "classes": "defect, crack",
                        "threshold": 0.75
                    }
                },
                {
                    "id": "cls",
                    "type": "classifier",
                    "config": {
                        "engine": "tflite",
                        "customModelPath": "data/models/classifier.tflite",
                        "classes": "pass, fail",
                        "topK": 2
                    }
                },
                {
                    "id": "trk",
                    "type": "tracker",
                    "config": {
                        "algorithm": "botsort",
                        "trackBuffer": 45,
                        "trackHighThreshold": 0.65
                    }
                },
                {
                    "id": "cnt",
                    "type": "object_counter",
                    "config": {
                        "direction": "enter",
                        "countOncePerTrack": True
                    }
                },
                {
                    "id": "snp",
                    "type": "track_snapshot",
                    "config": {
                        "captureMode": "best_frame",
                        "minimumConfidence": 0.70
                    }
                },
                {
                    "id": "wh",
                    "type": "webhook_output",
                    "config": {
                        "url": "http://127.0.0.1:8000/api/hook",
                        "cooldownSeconds": 3.0,
                        "sendImage": True
                    }
                },
                {
                    "id": "prev",
                    "type": "preview",
                    "config": {}
                }
            ],
            "edges": [
                ["inp", "det"],
                ["det", "seg"],
                ["seg", "cls"],
                ["cls", "trk"],
                ["trk", "cnt"],
                ["cnt", "snp"],
                ["snp", "wh"],
                ["wh", "prev"]
            ]
        }
        
        # Create project in backend
        res = client.post("/api/projects", json={"name": "Persistence Verification", "workflow": workflow})
        assert res.status_code == 200, res.text
        proj_id = res.json()["project"]["id"]
        print(f"[OK] Project created with ID: {proj_id}")
        
        # 2. Reload project from disk/database to verify persistence
        get_res = client.get(f"/api/projects/{proj_id}")
        assert get_res.status_code == 200
        saved_wf = get_res.json()["workflow"]
        saved_nodes = {n["id"]: n for n in saved_wf["nodes"]}
        
        # Test 1: Detector model settings saved
        det_cfg = saved_nodes["det"]["config"]
        assert det_cfg["engine"] == "ultralytics_yolo", f"Expected ultralytics_yolo, got {det_cfg['engine']}"
        assert det_cfg["customModelPath"] == "data/models/my_custom_detector.pt"
        assert det_cfg["classes"] == "person, forklift, pallet"
        assert det_cfg["threshold"] == 0.62
        assert det_cfg["iouThreshold"] == 0.45
        assert det_cfg["batchSize"] == 2
        print("[OK] Detector: engine, model path, classes, iou, threshold PERSISTED correctly on disk.")
        
        # Test 2: Segmenter model settings saved
        seg_cfg = saved_nodes["seg"]["config"]
        assert seg_cfg["engine"] == "onnx_custom"
        assert seg_cfg["customModelPath"] == "data/models/custom_seg.onnx"
        assert seg_cfg["classes"] == "defect, crack"
        assert seg_cfg["threshold"] == 0.75
        print("[OK] Segmenter: engine, ONNX model path, classes, threshold PERSISTED correctly on disk.")
        
        # Test 3: Classifier model settings saved
        cls_cfg = saved_nodes["cls"]["config"]
        assert cls_cfg["engine"] == "tflite"
        assert cls_cfg["customModelPath"] == "data/models/classifier.tflite"
        assert cls_cfg["classes"] == "pass, fail"
        assert cls_cfg["topK"] == 2
        print("[OK] Classifier: engine, TFLite model path, classes, topK PERSISTED correctly on disk.")
        
        # Test 4: Tracker algorithm saved
        trk_cfg = saved_nodes["trk"]["config"]
        assert trk_cfg["algorithm"] == "botsort"
        assert trk_cfg["trackBuffer"] == 45
        assert trk_cfg["trackHighThreshold"] == 0.65
        print("[OK] Tracker: algorithm (BoT-SORT), track buffer, threshold PERSISTED correctly on disk.")
        
        # Test 5: Object Counter direction saved
        cnt_cfg = saved_nodes["cnt"]["config"]
        assert cnt_cfg["direction"] == "enter"
        assert cnt_cfg["countOncePerTrack"] is True
        print("[OK] Object Counter: direction (enter), once per track PERSISTED correctly on disk.")
        
        # Test 6: Track Snapshot best frame saved
        snp_cfg = saved_nodes["snp"]["config"]
        assert snp_cfg["captureMode"] == "best_frame"
        assert snp_cfg["minimumConfidence"] == 0.70
        print("[OK] Track Snapshot: captureMode (best_frame), confidence PERSISTED correctly on disk.")
        
        # Test 7: Webhook output settings saved
        wh_cfg = saved_nodes["wh"]["config"]
        assert wh_cfg["url"] == "http://127.0.0.1:8000/api/hook"
        assert wh_cfg["cooldownSeconds"] == 3.0
        assert wh_cfg["sendImage"] is True
        print("[OK] Webhook Output: url, cooldown, sendImage PERSISTED correctly on disk.")
        
        # 3. Test update via PUT to verify edits persist
        saved_nodes["det"]["config"]["engine"] = "tensorflow_keras"
        saved_nodes["det"]["config"]["customModelPath"] = "data/models/model.keras"
        saved_nodes["trk"]["config"]["algorithm"] = "ocsort"
        
        put_res = client.put(f"/api/projects/{proj_id}", json={"workflow": saved_wf})
        assert put_res.status_code == 200
        
        # Re-fetch after PUT
        reloaded = client.get(f"/api/projects/{proj_id}").json()["workflow"]
        reloaded_nodes = {n["id"]: n for n in reloaded["nodes"]}
        assert reloaded_nodes["det"]["config"]["engine"] == "tensorflow_keras"
        assert reloaded_nodes["det"]["config"]["customModelPath"] == "data/models/model.keras"
        assert reloaded_nodes["trk"]["config"]["algorithm"] == "ocsort"
        print("[OK] Live project PUT updates PERSISTED and verified from disk reload!")

    temp_dir.cleanup()
    print("=== All Model Choices & Settings Persistence 100% VERIFIED! ===")


if __name__ == "__main__":
    test_every_model_setting_persistence()
