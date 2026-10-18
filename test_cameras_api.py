from fastapi.testclient import TestClient
from server import app, store, _CAMERAS_FILE

client = TestClient(app, base_url="http://127.0.0.1:8765")


def test_get_cctv_cameras():
    res = client.get("/api/cctv-cameras")
    assert res.status_code == 200
    data = res.json()
    assert "cameras" in data
    assert data["count"] >= 8
    # WS-01 should be present
    ws01 = next((c for c in data["cameras"] if c["id"] == "WS-01"), None)
    assert ws01 is not None
    assert ws01["type"] == "workshop"
    assert "rtsp://" in ws01["streamUrl"]


def test_update_cctv_camera():
    res = client.put("/api/cctv-cameras/WS-02", json={
        "name": "Workshop Bay 2 Updated",
        "streamUrl": "rtsp://192.168.1.199:554/live",
        "resolution": "4K",
        "fps": 30.0,
    })
    assert res.status_code == 200
    cam = res.json()["camera"]
    assert cam["name"] == "Workshop Bay 2 Updated"
    assert cam["streamUrl"] == "rtsp://192.168.1.199:554/live"
    assert cam["resolution"] == "4K"
    assert cam["fps"] == 30.0

    # Cleanup: restore standard values
    client.put("/api/cctv-cameras/WS-02", json={
        "name": "Workshop Bay 2",
        "streamUrl": "rtsp://192.168.1.102:554/live",
        "resolution": "1080p",
        "fps": 0.0,
    })


def test_create_and_delete_custom_camera():
    # Create
    res = client.post("/api/cctv-cameras", json={
        "name": "New Inspection Bay 6",
        "type": "workshop",
        "streamUrl": "rtsp://192.168.1.106:554/live",
        "resolution": "1080p",
        "fps": 25.0,
    })
    assert res.status_code == 200
    cam = res.json()["camera"]
    cam_id = cam["id"]
    assert cam["name"] == "New Inspection Bay 6"
    assert cam.get("isCustom") is True

    # Delete
    del_res = client.delete(f"/api/cctv-cameras/{cam_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True


def test_create_camera_workflow_auto():
    # Create workflow from template for WH-01
    res = client.post("/api/cctv-cameras/WH-01/create-workflow")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "project" in data
    assert "workflow" in data
    assert data["camera"]["assignedProjectId"] == data["project"]["id"]

    # Verify project has ip_camera node matching camera streamUrl
    nodes = data["workflow"]["nodes"]
    ip_cam_node = next((n for n in nodes if n["type"] == "ip_camera"), None)
    assert ip_cam_node is not None
    assert ip_cam_node["config"]["streamUrl"] == data["camera"]["streamUrl"]

    # Cleanup: delete created project and reset camera assignment
    proj_id = data["project"]["id"]
    client.delete(f"/api/projects/{proj_id}")
    client.put("/api/cctv-cameras/WH-01", json={"assignedProjectId": ""})
