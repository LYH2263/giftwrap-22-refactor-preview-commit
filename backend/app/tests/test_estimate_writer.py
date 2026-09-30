"""落档写入器测例：可写可读的临时 SQLite 库。

覆盖成功写入、按编号读回一致、脏盒拒绝；并钉住
试算 / 落档读回 / 列表摘要 / 详情 四处数值一致。
"""

import pytest
from fastapi import HTTPException

from app import seed
from app.db import connect
from app.repositories import history
from app.routers.estimates import get_est, post_est
from app.routers.history_router import run_detail, runs
from app.schemas.estimate import EstimateRequest
from app.services import estimate_core, estimate_writer

DIMS = {"length": 0.30, "width": 0.20, "height": 0.15}


@pytest.fixture
def db(tmp_path, monkeypatch):
    """每个测例一座全新的临时库：建表后清场，用哪行插哪行。"""
    monkeypatch.setattr("app.db.DB_PATH", tmp_path / "test.db")
    seed.init_db()
    c = connect()
    try:
        c.executescript("DELETE FROM calc_runs; DELETE FROM boxes; DELETE FROM papers; DELETE FROM settings;")
        c.commit()
    finally:
        c.close()
    yield


def _insert_box(name, quality, l=DIMS["length"], w=DIMS["width"], h=DIMS["height"]):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO boxes(name,length,width,height,data_quality,note) VALUES (?,?,?,?,?,?)",
            (name, l, w, h, quality, ""),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def _set_overlap(value):
    c = connect()
    try:
        c.execute("INSERT OR REPLACE INTO settings(key,value) VALUES ('overlap',?)", (str(value),))
        c.commit()
    finally:
        c.close()


def test_save_estimate_success_then_read_back_by_id(db):
    bid = _insert_box("书型盒", "clean")
    saved = estimate_writer.save_estimate(bid, 1.2, "cross", "礼单")
    assert saved["run_id"]
    assert saved["box"]["id"] == bid

    expected = estimate_core.estimate(DIMS, 1.2, "cross")
    assert saved["paper_m2"] == expected["paper_m2"]
    assert saved["ribbon"] == expected["ribbon"]

    row = history.get_run(saved["run_id"])
    assert row["box_id"] == bid
    assert row["overlap"] == 1.2
    assert row["note"] == "礼单"
    assert row["result"]["paper_m2"] == expected["paper_m2"]
    assert row["result"]["ribbon"] == expected["ribbon"]


def test_save_estimate_uses_settings_overlap_when_omitted(db):
    _set_overlap(1.3)
    bid = _insert_box("默认系数盒", "clean")
    saved = estimate_writer.save_estimate(bid, None, "band")
    assert saved["overlap"] == pytest.approx(1.3)
    assert history.get_run(saved["run_id"])["overlap"] == pytest.approx(1.3)


def test_save_estimate_rejects_dirty_box_and_writes_nothing(db):
    bid = _insert_box("脏盒-负高", "dirty", h=-0.1)
    before = len(history.list_runs())
    with pytest.raises(estimate_writer.DirtyBoxError):
        estimate_writer.save_estimate(bid, 1.2, "cross")
    assert len(history.list_runs()) == before


def test_save_estimate_missing_box(db):
    with pytest.raises(estimate_writer.BoxNotFoundError):
        estimate_writer.save_estimate(987654, 1.2, "cross")


def test_list_summary_and_detail_pin_same_numbers(db):
    bid = _insert_box("一致盒", "clean")
    saved = estimate_writer.save_estimate(bid, 1.2, "cross")
    detail = history.get_run(saved["run_id"])
    summary = next(r for r in history.list_runs() if r["id"] == saved["run_id"])
    assert summary["result"]["paper_m2"] == detail["result"]["paper_m2"] == saved["paper_m2"]
    assert summary["result"]["ribbon"] == detail["result"]["ribbon"] == saved["ribbon"]


def test_http_trial_save_and_readback_pin_same_numbers(db):
    bid = _insert_box("全链路盒", "clean")
    trial = get_est(box_id=bid, overlap=1.2, wrap_style="cross")
    assert trial["run_id"] is None
    saved = post_est(EstimateRequest(box_id=bid, overlap=1.2, wrap_style="cross", save=True, note="钉数"))
    assert saved["run_id"]

    detail = run_detail(saved["run_id"])
    summary = next(item for item in runs()["items"] if item["id"] == saved["run_id"])
    assert trial["paper_m2"] == saved["paper_m2"] == detail["result"]["paper_m2"] == summary["result"]["paper_m2"]
    assert trial["ribbon"] == saved["ribbon"] == detail["result"]["ribbon"] == summary["result"]["ribbon"]


def test_http_dirty_box_rejected_422(db):
    bid = _insert_box("脏盒", "dirty", h=-0.1)
    with pytest.raises(HTTPException) as trial_err:
        get_est(box_id=bid)
    assert trial_err.value.status_code == 422
    with pytest.raises(HTTPException) as save_err:
        post_est(EstimateRequest(box_id=bid, save=True))
    assert save_err.value.status_code == 422


def test_http_missing_box_404(db):
    with pytest.raises(HTTPException) as exc_info:
        get_est(box_id=424242)
    assert exc_info.value.status_code == 404
