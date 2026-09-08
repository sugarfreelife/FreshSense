from app.sensors.service import validate_reading


def test_valid_reading():
    ok, errors = validate_reading(gas_value=200.0, temperature=25.0, humidity=50.0)
    assert ok and errors == []


def test_out_of_range():
    ok, errors = validate_reading(gas_value=99999.0)
    assert not ok and errors


def test_empty_rejected():
    ok, errors = validate_reading()
    assert not ok


def test_sensor_endpoints(client, auth_headers):
    r = client.post("/api/v1/sensors/readings", json={"gas_value": 150.0, "temperature": 24.0, "humidity": 55.0}, headers=auth_headers)
    assert r.status_code == 201, r.text
    lst = client.get("/api/v1/sensors/readings", headers=auth_headers)
    assert lst.status_code == 200
    assert len(lst.json()) >= 1


def test_sensor_invalid_rejected(client, auth_headers):
    r = client.post("/api/v1/sensors/readings", json={"gas_value": 99999.0}, headers=auth_headers)
    assert r.status_code == 400
