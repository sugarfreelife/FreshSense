import uuid


def _reg(client, email=None):
    email = email or f"u_{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "pass1234"})
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["access_token"], body  # register auto-logs in (frontend contract)
    assert body["user"]["email"] == email, body
    return email


def test_register_login_me(client):
    email = _reg(client)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "pass1234"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    assert token
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_login_wrong_password(client):
    email = _reg(client)
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
    assert r.status_code == 401


def test_me_unauthorized(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
