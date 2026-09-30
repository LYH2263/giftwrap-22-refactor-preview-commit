"""HTTP 处理器测例：试算与写入两个入口，及用纸档详情的状态码与钉值。"""
import pytest
from fastapi.testclient import TestClient

from app import seed
from app.db import connect
from app.main import app


@pytest.fixture(autouse=True)
def fresh_db():
    seed.init_db()
    c = connect()
    c.execute("DELETE FROM calc_runs")
    c.commit()
    c.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_preview_entry_does_not_write(client):
    r = client.get("/api/estimate", params={"box_id": 1, "overlap": 1.15})
    assert r.status_code == 200
    body = r.json()
    assert "run_id" not in body
    assert body["paper_m2"] == 0.31
    assert client.get("/api/runs").json()["items"] == []


def test_save_entry_writes_and_detail_pins_same_numbers(client):
    saved = client.post("/api/estimate", json={
        "box_id": 2, "overlap": 1.20, "wrap_style": "cross", "note": "n",
    })
    assert saved.status_code == 200
    s = saved.json()
    rid = s["run_id"]
    assert isinstance(rid, int)

    preview = client.get("/api/estimate",
                         params={"box_id": 2, "overlap": 1.20}).json()
    detail = client.get(f"/api/runs/{rid}")
    assert detail.status_code == 200
    d = detail.json()
    lst = client.get("/api/runs").json()["items"]
    summary = next(x for x in lst if x["id"] == rid)

    assert preview["paper_m2"] == s["paper_m2"] == d["paper_m2"] == summary["paper_m2"]
    assert preview["ribbon_m"] == s["ribbon_m"] == d["ribbon_m"] == summary["ribbon_m"]


def test_dirty_and_missing_box_status_codes(client):
    assert client.post("/api/estimate", json={"box_id": 3}).status_code == 422
    assert client.get("/api/estimate", params={"box_id": 999}).status_code == 404
    assert client.get("/api/runs/99999").status_code == 404
