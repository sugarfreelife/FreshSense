import uuid


def _register(client, email: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass1234", "name": email.split("@", 1)[0]},
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_business_workspace_shares_stock_without_leaking_personal_batches(client):
    owner_email = f"owner_{uuid.uuid4().hex[:8]}@example.com"
    staff_email = f"staff_{uuid.uuid4().hex[:8]}@example.com"
    outsider_email = f"outsider_{uuid.uuid4().hex[:8]}@example.com"
    owner = _register(client, owner_email)
    staff = _register(client, staff_email)
    outsider = _register(client, outsider_email)

    personal = client.post(
        "/api/v1/inventory",
        headers=owner,
        json={"product_name": "Private pantry batch", "quantity": 2, "expiry_source": "unknown"},
    )
    assert personal.status_code == 201, personal.text

    workspace_response = client.post("/api/v1/workspaces", headers=owner, json={"name": "North Market"})
    assert workspace_response.status_code == 201, workspace_response.text
    workspace = workspace_response.json()
    assert workspace["role"] == "owner"
    workspace_headers = {
        **owner,
        "X-Workspace-Mode": "business",
        "X-Workspace-Id": workspace["id"],
    }

    member_response = client.post(
        f"/api/v1/workspaces/{workspace['id']}/members",
        headers=owner,
        json={"email": staff_email, "role": "staff"},
    )
    assert member_response.status_code == 201, member_response.text
    member_id = member_response.json()["id"]

    stock_response = client.post(
        "/api/v1/inventory",
        headers=workspace_headers,
        json={
            "product_name": "Canned beans",
            "quantity": 12,
            "expiry_source": "unknown",
            "stock_location": "Store 2 · Cold room",
        },
    )
    assert stock_response.status_code == 201, stock_response.text
    stock = stock_response.json()
    assert stock["stock_location"] == "Store 2 · Cold room"

    personal_rows = client.get("/api/v1/inventory", headers=owner).json()
    assert [row["product_name"] for row in personal_rows] == ["Private pantry batch"]

    staff_workspace_headers = {**workspace_headers, "Authorization": staff["Authorization"]}
    staff_rows = client.get("/api/v1/inventory", headers=staff_workspace_headers)
    assert staff_rows.status_code == 200, staff_rows.text
    assert [row["product_name"] for row in staff_rows.json()] == ["Canned beans"]

    changed = client.patch(
        f"/api/v1/inventory/{stock['id']}",
        headers=staff_workspace_headers,
        json={"quantity": 9},
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["quantity"] == 9

    assert client.get("/api/v1/inventory", headers={**workspace_headers, "Authorization": outsider["Authorization"]}).status_code == 404
    assert client.patch(
        f"/api/v1/inventory/{personal.json()['id']}",
        headers=staff_workspace_headers,
        json={"quantity": 1},
    ).status_code == 404
    assert client.delete(f"/api/v1/inventory/{stock['id']}", headers=staff_workspace_headers).status_code == 403
    assert client.delete(
        f"/api/v1/workspaces/{workspace['id']}/members/{member_id}", headers=owner
    ).status_code == 204

