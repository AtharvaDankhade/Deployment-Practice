"""API tests - these double as the contract the container smoke test checks."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_readyz_reports_version():
    res = client.get("/readyz")
    assert res.status_code == 200
    assert res.json()["status"] == "ready"
    assert "version" in res.json()


def test_index_serves_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_calculate_success():
    res = client.post("/api/calculate", json={"operation": "multiply", "a": 6, "b": 7})
    assert res.status_code == 200
    assert res.json() == {"operation": "multiply", "a": 6, "b": 7, "result": 42}


def test_calculate_returns_request_id():
    res = client.post("/api/calculate", json={"operation": "add", "a": 1, "b": 1})
    assert res.headers["x-request-id"]


def test_calculate_echoes_request_id():
    res = client.get("/healthz", headers={"x-request-id": "abc123"})
    assert res.headers["x-request-id"] == "abc123"


def test_divide_by_zero_is_400():
    res = client.post("/api/calculate", json={"operation": "divide", "a": 1, "b": 0})
    assert res.status_code == 400
    assert "divide by zero" in res.json()["detail"]


def test_invalid_operation_is_422():
    res = client.post("/api/calculate", json={"operation": "pow", "a": 2, "b": 3})
    assert res.status_code == 422


def test_missing_field_is_422():
    res = client.post("/api/calculate", json={"operation": "add", "a": 2})
    assert res.status_code == 422


@pytest.mark.parametrize("metric", ["http_requests_total", "calculator_operations_total"])
def test_metrics_exposed(metric):
    client.post("/api/calculate", json={"operation": "add", "a": 2, "b": 2})
    res = client.get("/metrics")
    assert res.status_code == 200
    assert metric in res.text
