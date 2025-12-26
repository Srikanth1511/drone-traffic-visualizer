"""
Unit tests for Live Telemetry System

This test suite proves that the drone visualization backend works correctly
for live telemetry streaming and video frame handling.

Run with: pytest tests/test_live_telemetry.py -v
"""

import pytest
import requests
import io

# Backend URL for testing
BASE_URL = "http://localhost:8000"


@pytest.fixture
def client():
    """Return base URL for making HTTP requests"""
    return BASE_URL


class TestBackendHealth:
    """Test suite for backend health and status endpoints"""

    def test_health_endpoint(self, client):
        """Verify backend health check endpoint returns 200 OK"""
        response = requests.get(f"{client}/api/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_response_structure(self, client):
        """Verify health endpoint returns expected fields"""
        response = requests.get(f"{client}/api/health")
        data = response.json()

        assert "status" in data
        assert "playback_loaded" in data
        assert "scenario_loaded" in data


class TestDroneRegistration:
    """Test suite for drone registration functionality"""

    def test_register_drone_success(self, client):
        """Verify drone can be registered successfully"""
        payload = {
            "drone_id": "test_drone_001",
            "metadata": {
                "type": "dji",
                "model": "Mini 3"
            }
        }

        response = requests.post(f"{client}/api/drones/register", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["drone_id"] == "test_drone_001"
        assert data["status"] == "registered"
        assert "registered_at" in data

    def test_register_drone_minimal(self, client):
        """Verify drone registration with minimal data"""
        payload = {
            "drone_id": "minimal_drone_001"
        }

        response = requests.post(f"{client}/api/drones/register", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["drone_id"] == "minimal_drone_001"
        assert data["status"] == "registered"

    def test_unregister_drone(self, client):
        """Verify drone can be unregistered"""
        # First register
        requests.post(f"{client}/api/drones/register", json={"drone_id": "temp_drone_001"})

        # Then unregister
        response = requests.delete(f"{client}/api/drones/temp_drone_001")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["drone_id"] == "temp_drone_001"


class TestLiveTelemetry:
    """Test suite for live telemetry updates"""

    def test_telemetry_update_http(self, client):
        """Verify telemetry can be sent via HTTP POST"""
        telemetry = {
            "id": "test_drone_002",
            "lat": 33.7736,
            "lon": -84.4022,
            "alt_msl": 350.0,
            "alt_agl": 50.0,
            "heading": 180.0,
            "speed": 5.5,
            "health": "OK",
            "link_quality": 0.95,
            "vertical_speed": 0.0,
            "payload": {
                "battery": 0.85
            }
        }

        response = requests.post(f"{client}/api/telemetry/live/update", json=telemetry)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test_drone_002"
        assert data["lat"] == 33.7736
        assert data["lon"] == -84.4022
        assert data["alt_agl"] == 50.0
        assert data["heading"] == 180.0
        assert data["health"] == "OK"

    def test_telemetry_update_minimal_required_fields(self, client):
        """Verify telemetry update with only required fields"""
        telemetry = {
            "id": "test_drone_003",
            "lat": 33.7736,
            "lon": -84.4022,
            "alt_msl": 350.0,
            "alt_agl": 50.0,
            "heading": 90.0,
            "speed": 10.0
        }

        response = requests.post(f"{client}/api/telemetry/live/update", json=telemetry)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == "test_drone_003"
        assert data["health"] == "OK"  # Should default to OK
        assert data["linkQuality"] == 1.0  # Should default to 1.0

    def test_get_current_telemetry(self, client):
        """Verify current telemetry state can be retrieved"""
        # Send some telemetry first
        telemetry = {
            "id": "test_drone_004",
            "lat": 33.7736,
            "lon": -84.4022,
            "alt_msl": 350.0,
            "alt_agl": 50.0,
            "heading": 270.0,
            "speed": 7.5,
            "health": "OK"
        }
        requests.post(f"{client}/api/telemetry/live/update", json=telemetry)

        # Retrieve current state
        response = requests.get(f"{client}/api/telemetry/live/current")
        assert response.status_code == 200

        data = response.json()
        assert "time" in data
        assert "drones" in data
        assert isinstance(data["drones"], list)

        # Find our drone
        drone_found = any(d["id"] == "test_drone_004" for d in data["drones"])
        assert drone_found, "Drone should appear in current telemetry"

    def test_telemetry_with_full_payload(self, client):
        """Verify telemetry with complete payload data"""
        telemetry = {
            "id": "test_drone_005",
            "lat": 33.7736,
            "lon": -84.4022,
            "alt_msl": 350.0,
            "alt_agl": 50.0,
            "heading": 45.0,
            "speed": 12.0,
            "health": "OK",
            "link_quality": 0.89,
            "vertical_speed": 2.5,
            "payload": {
                "battery": 0.72,
                "cameraStreams": ["rtsp://example.com/stream"],
                "gimbalYaw": 10.0,
                "gimbalPitch": -30.0,
                "thermalEnabled": True
            }
        }

        response = requests.post(f"{client}/api/telemetry/live/update", json=telemetry)
        assert response.status_code == 200

        data = response.json()
        assert data["payload"]["battery"] == 0.72
        assert len(data["payload"]["cameraStreams"]) == 1
        assert data["payload"]["gimbalYaw"] == 10.0
        assert data["payload"]["gimbalPitch"] == -30.0
        assert data["payload"]["thermalEnabled"] is True


class TestVideoStreaming:
    """Test suite for video frame upload and retrieval"""

    def test_upload_video_frame(self, client):
        """Verify video frame can be uploaded"""
        # Create a fake JPEG frame
        fake_jpeg = b'\xff\xd8\xff\xe0' + b'\x00' * 96 + b'\xff\xd9'  # Minimal JPEG

        files = {"frame": ("frame.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
        response = requests.post(f"{client}/api/video/test_drone_006/frame", files=files)

        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["drone_id"] == "test_drone_006"
        assert data["frame_size"] == len(fake_jpeg)

    def test_retrieve_video_frame(self, client):
        """Verify uploaded video frame can be retrieved"""
        # Upload a frame first
        fake_jpeg = b'\xff\xd8\xff\xe0' + b'\x00' * 96 + b'\xff\xd9'
        files = {"frame": ("frame.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
        requests.post(f"{client}/api/video/test_drone_007/frame", files=files)

        # Retrieve the frame
        response = requests.get(f"{client}/api/video/test_drone_007/frame")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) == len(fake_jpeg)
        assert response.content == fake_jpeg

    def test_retrieve_nonexistent_video_frame(self, client):
        """Verify 404 when requesting frame for drone with no video"""
        response = requests.get(f"{client}/api/video/nonexistent_drone/frame")
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "No video frame available" in data["detail"]

    def test_mjpeg_stream_endpoint_exists(self, client):
        """Verify MJPEG stream endpoint is accessible"""
        # Upload a frame first
        fake_jpeg = b'\xff\xd8\xff\xe0' + b'\x00' * 96 + b'\xff\xd9'
        files = {"frame": ("frame.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
        requests.post(f"{client}/api/video/test_drone_008/frame", files=files)

        # Test MJPEG endpoint (just check it's accessible, don't wait for stream)
        response = requests.get(f"{client}/api/video/test_drone_008/stream.mjpeg",
                               timeout=0.5,
                               stream=True)

        # MJPEG streams return 200 and multipart content-type
        assert response.status_code == 200
        assert "multipart/x-mixed-replace" in response.headers["content-type"]


class TestEndToEndFlow:
    """Test suite for complete end-to-end workflows"""

    def test_complete_drone_lifecycle(self, client):
        """Test complete flow: register → telemetry → video → unregister"""
        drone_id = "e2e_drone_001"

        # 1. Register drone
        register_response = requests.post(f"{client}/api/drones/register", json={
            "drone_id": drone_id,
            "metadata": {"type": "dji", "model": "Mini 3"}
        })
        assert register_response.status_code == 200

        # 2. Send telemetry
        telemetry_response = requests.post(f"{client}/api/telemetry/live/update", json={
            "id": drone_id,
            "lat": 33.7736,
            "lon": -84.4022,
            "alt_msl": 350.0,
            "alt_agl": 50.0,
            "heading": 90.0,
            "speed": 5.0,
            "health": "OK",
            "payload": {"battery": 0.95}
        })
        assert telemetry_response.status_code == 200

        # 3. Upload video frame
        fake_jpeg = b'\xff\xd8\xff\xe0' + b'\x00' * 96 + b'\xff\xd9'
        files = {"frame": ("frame.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}
        video_response = requests.post(f"{client}/api/video/{drone_id}/frame", files=files)
        assert video_response.status_code == 200

        # 4. Verify current state includes drone
        current_response = requests.get(f"{client}/api/telemetry/live/current")
        current_data = current_response.json()
        drone_found = any(d["id"] == drone_id for d in current_data["drones"])
        assert drone_found

        # 5. Retrieve video frame
        frame_response = requests.get(f"{client}/api/video/{drone_id}/frame")
        assert frame_response.status_code == 200
        assert frame_response.content == fake_jpeg

        # 6. Unregister drone
        unregister_response = requests.delete(f"{client}/api/drones/{drone_id}")
        assert unregister_response.status_code == 200

    def test_multiple_drones_simultaneously(self, client):
        """Test handling multiple drones at once"""
        drones = ["multi_drone_001", "multi_drone_002", "multi_drone_003"]

        # Register all drones
        for drone_id in drones:
            response = requests.post(f"{client}/api/drones/register", json={"drone_id": drone_id})
            assert response.status_code == 200

        # Send telemetry for all drones
        for i, drone_id in enumerate(drones):
            response = requests.post(f"{client}/api/telemetry/live/update", json={
                "id": drone_id,
                "lat": 33.7736 + i * 0.01,
                "lon": -84.4022 + i * 0.01,
                "alt_msl": 350.0,
                "alt_agl": 50.0,
                "heading": 90.0 + i * 30,
                "speed": 5.0 + i,
                "health": "OK"
            })
            assert response.status_code == 200

        # Verify all drones in current state
        response = requests.get(f"{client}/api/telemetry/live/current")
        data = response.json()

        drone_ids = [d["id"] for d in data["drones"]]
        for drone_id in drones:
            assert drone_id in drone_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
