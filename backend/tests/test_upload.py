import io

from PIL import Image


def _img_bytes(color=(200, 50, 50)):
    img = Image.new("RGB", (64, 64), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_upload_and_crud(client, auth_headers):
    files = {"file": ("apple.png", _img_bytes(), "image/png")}
    r = client.post("/api/v1/scans", files=files, headers=auth_headers)
    assert r.status_code == 201, r.text
    scan_id = r.json()["id"]

    lst = client.get("/api/v1/scans", headers=auth_headers)
    assert lst.status_code == 200 and len(lst.json()) >= 1

    one = client.get(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert one.status_code == 200
    assert one.json()["assessment"] is not None

    asmt = client.get(f"/api/v1/assessments/{scan_id}", headers=auth_headers)
    assert asmt.status_code == 200

    d = client.delete(f"/api/v1/scans/{scan_id}", headers=auth_headers)
    assert d.status_code == 200


def test_upload_rejects_bad_extension(client, auth_headers):
    files = {"file": ("evil.txt", io.BytesIO(b"hello"), "text/plain")}
    r = client.post("/api/v1/scans", files=files, headers=auth_headers)
    assert r.status_code == 400


def test_vision_endpoint(client, auth_headers):
    files = {"file": ("banana.png", _img_bytes((50, 200, 50)), "image/png")}
    r = client.post("/api/v1/predictions/vision", files=files, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["model_type"] == "prototype"
