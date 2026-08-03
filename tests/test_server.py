"""
Unit tests for CanaryFile Engine listener server endpoints.
"""

import pytest
import os
import sqlite3
from fastapi.testclient import TestClient

from server.main import app, db, rate_limiter
from server.config import settings


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path):
    """Fixture to isolate SQLite database for testing."""
    test_db_path = str(tmp_path / "test_canary.db")
    db.db_path = test_db_path
    db._init_db()
    rate_limiter.requests.clear()
    yield
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except PermissionError:
            pass


client = TestClient(app)


def test_healthcheck():
    """Verify healthcheck endpoint returns status 200 and application details."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_register_token():
    """Verify token registration via API."""
    payload = {
        "token_id": "unit-test-token-001",
        "label": "Confidential Finance Spec",
        "file_type": "pdf"
    }
    response = client.post("/api/v1/tokens", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["token_id"] == "unit-test-token-001"
    assert data["label"] == "Confidential Finance Spec"
    assert data["file_type"] == "pdf"


def test_canary_trigger_hit():
    """Verify triggering canary endpoint logs hit data and returns 1x1 GIF."""
    token_id = "test-trigger-xyz"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Test-Agent)",
        "X-Forwarded-For": "198.51.100.42"
    }
    
    response = client.get(f"/t/{token_id}", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/gif"
    assert len(response.content) > 0

    # Verify hit is recorded in database
    hits = db.list_hits(token_id=token_id)
    assert len(hits) == 1
    hit = hits[0]
    assert hit["token_id"] == token_id
    assert hit["src_ip"] == "198.51.100.42"
    assert hit["user_agent"] == "Mozilla/5.0 (Test-Agent)"


def test_list_tokens_and_hits():
    """Verify listing endpoints return expected records."""
    client.post("/api/v1/tokens", json={"token_id": "tok-1", "label": "Label 1"})
    client.get("/t/tok-1")

    tokens = client.get("/api/v1/tokens").json()
    assert len(tokens) >= 1
    assert any(t["token_id"] == "tok-1" for t in tokens)

    hits = client.get("/api/v1/hits").json()
    assert len(hits) >= 1
    assert any(h["token_id"] == "tok-1" for h in hits)


def test_trigger_test_prefixed_endpoints():
    """Verify endpoints work with /trigger-test route prefix."""
    payload = {
        "token_id": "prefixed-token-777",
        "label": "Prefixed Route Test",
        "file_type": "pdf"
    }
    response = client.post("/trigger-test/api/v1/tokens", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["token_id"] == "prefixed-token-777"

    headers = {
        "User-Agent": "Mozilla/5.0 (Prefixed-Agent)",
        "X-Forwarded-For": "203.0.113.195"
    }
    hit_resp = client.get("/trigger-test/t/prefixed-token-777", headers=headers)
    assert hit_resp.status_code == 200
    assert hit_resp.headers["content-type"] == "image/gif"

    hits = client.get("/trigger-test/api/v1/hits?token_id=prefixed-token-777").json()
    assert len(hits) == 1
    assert hits[0]["token_id"] == "prefixed-token-777"
    assert hits[0]["src_ip"] == "203.0.113.195"


def test_api_key_authentication():
    """Verify management endpoints return 401 when API key is required but missing/invalid."""
    settings.api_key = "super-secret-key"
    try:
        # Request without header -> 401
        res_no_auth = client.get("/api/v1/tokens")
        assert res_no_auth.status_code == 401

        # Request with invalid header -> 401
        res_invalid_auth = client.get("/api/v1/tokens", headers={"X-API-Key": "wrong-key"})
        assert res_invalid_auth.status_code == 401

        # Request with valid header -> 200
        res_valid_auth = client.get("/api/v1/tokens", headers={"X-API-Key": "super-secret-key"})
        assert res_valid_auth.status_code == 200
    finally:
        settings.api_key = None


def test_rate_limiting():
    """Verify trigger endpoint returns 429 when rate limit per IP is exceeded."""
    settings.rate_limit_per_minute = 3
    headers = {"X-Forwarded-For": "198.51.100.99"}
    try:
        for i in range(3):
            res = client.get("/t/rate-tok", headers=headers)
            assert res.status_code == 200

        # 4th request should exceed rate limit
        res_blocked = client.get("/t/rate-tok", headers=headers)
        assert res_blocked.status_code == 429
        assert "Rate limit exceeded" in res_blocked.json()["detail"]
    finally:
        settings.rate_limit_per_minute = 60
        rate_limiter.requests.clear()
