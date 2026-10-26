import uuid

from app.core.config import settings


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


def test_browser_session_cookie_and_csrf_protected_logout(client):
    email = _reg(client)
    session_token = client.cookies.get("freshsense_session")
    csrf_cookie = client.cookies.get("freshsense_csrf")
    assert session_token
    assert csrf_cookie

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == email

    missing_csrf = client.post("/api/v1/auth/logout")
    assert missing_csrf.status_code == 403

    logout = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_cookie})
    assert logout.status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401
    bearer_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {session_token}"})
    assert bearer_me.status_code == 401


def test_bearer_logout_revokes_token_without_browser_csrf(client):
    _reg(client)
    token = client.cookies.get("freshsense_session")
    assert token
    client.cookies.clear()

    logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 204
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 401


def test_production_login_uses_secure_httponly_cookie_and_omits_token(client, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    response = client.post(
        "/api/v1/auth/register",
        json={"email": f"prod_{uuid.uuid4().hex[:8]}@example.com", "password": "pass1234"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["access_token"] is None
    cookies = response.headers.get_list("set-cookie")
    session_cookie = next(value for value in cookies if value.startswith("freshsense_session="))
    csrf_cookie = next(value for value in cookies if value.startswith("freshsense_csrf="))
    assert "httponly" in session_cookie.lower()
    assert "secure" in session_cookie.lower()
    assert "samesite=strict" in session_cookie.lower()
    assert "secure" in csrf_cookie.lower()


def test_login_rate_limit_returns_retry_after(client):
    for _ in range(10):
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    blocked = client.post(
        "/api/v1/auth/login",
        json={"email": "missing@example.com", "password": "wrong-password"},
    )
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
