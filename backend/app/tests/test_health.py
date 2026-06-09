"""Smoke tests for the minimal runnable backend."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["app"] == "DormMove AI"


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ping():
    resp = client.get("/api/v1/ping")
    assert resp.status_code == 200
    assert resp.json()["message"] == "pong"
