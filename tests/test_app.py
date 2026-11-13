from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import rescam.campaigns as campaigns
import rescam.storage as storage
from rescam.server import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "rescam.sqlite3")
    monkeypatch.setattr(campaigns, "DATA_DIR", tmp_path)
    monkeypatch.setenv("RESCAM_PUBLIC_URL", "https://demo.example")
    monkeypatch.delenv("RESCAM_ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("RESCAM_ADMIN_PASSWORD", raising=False)
    return TestClient(app)


def test_amount_validation():
    assert campaigns.normalize_amount("0.0500") == "0.05"
    for invalid in ("0", "-1", "NaN", "Infinity", "abc", "0.0000000000000000001"):
        with pytest.raises(ValueError):
            campaigns.normalize_amount(invalid)


def test_dashboard_create_and_public_simulation(client):
    response = client.post(
        "/campaigns",
        data={
            "currency": "BTC",
            "amount": "0.05",
            "payment_method": "Example transfer",
            "note": "Training example",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    detail_url = response.headers["location"]
    campaign_id = detail_url.rsplit("/", 1)[-1]

    detail = client.get(detail_url)
    assert detail.status_code == 200
    assert "Campaign URL" in detail.text
    assert f"/c/{campaign_id}/qr.png" in detail.text

    qr = client.get(f"/c/{campaign_id}/qr.png")
    assert qr.status_code == 200
    assert qr.headers["content-type"] == "image/png"

    receipt = client.get(f"/c/{campaign_id}")
    assert receipt.status_code == 200
    assert "SIMULATION — NOT A REAL PAYMENT" in receipt.text
    assert "0.05" in receipt.text
    assert "No payment was made or verified" in receipt.text

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert "1 views" in dashboard.text


def test_remote_dashboard_requires_admin_credentials():
    remote_client = TestClient(app, client=("203.0.113.10", 12345))
    response = remote_client.get("/")
    assert response.status_code == 503


def test_remote_dashboard_accepts_configured_basic_auth(client, monkeypatch):
    monkeypatch.setenv("RESCAM_ADMIN_USERNAME", "operator")
    monkeypatch.setenv("RESCAM_ADMIN_PASSWORD", "test-password")
    remote_client = TestClient(app, client=("203.0.113.10", 12345))

    assert remote_client.get("/").status_code == 401
    response = remote_client.get("/", auth=("operator", "test-password"))
    assert response.status_code == 200
