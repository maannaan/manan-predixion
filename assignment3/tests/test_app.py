from fastapi.testclient import TestClient

from app.main import app


def test_health():
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


def test_webhook_busy_schedules_retry(monkeypatch, tmp_path):
    from app import main as main_mod

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "calls.db"))
    called = {}

    async def fake_notify(crm_url, account_id, next_call, attempts=5):
        called["next"] = next_call
        return {"status": "ok"}

    monkeypatch.setattr(main_mod, "notify_crm", fake_notify)
    with TestClient(app) as client:
        res = client.post(
            "/webhook/call-completed",
            json={"account_id": "A1", "disposition": "BUSY", "attempt": 0},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
        assert res.json()["next_call"] is not None
        assert "next" in called


def test_webhook_ptp_does_not_retry(monkeypatch, tmp_path):
    from app import main as main_mod

    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "calls.db"))
    called = {"n": 0}

    async def fake_notify(*_a, **_k):
        called["n"] += 1
        return {"status": "ok"}

    monkeypatch.setattr(main_mod, "notify_crm", fake_notify)
    with TestClient(app) as client:
        res = client.post(
            "/webhook/call-completed",
            json={"account_id": "A1", "disposition": "PTP", "attempt": 0},
        )
        assert res.status_code == 200
        assert res.json()["next_call"] is None
        assert called["n"] == 0
