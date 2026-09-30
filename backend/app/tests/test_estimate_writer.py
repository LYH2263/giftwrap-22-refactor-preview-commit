"""落档写入器测例：临时库上可写可读。

覆盖成功写入、脏盒拒绝、不存在、试算不落库，以及
「试算 == 落档响应 == 按编号读回 == 列表摘要」四处数字一致。
"""
import pytest

from app import seed
from app.repositories import history
from app.services import estimate_writer
from app.services.estimate_core import estimate_core
from app.services.estimate_writer import BoxNotFound, DirtyBox


@pytest.fixture(autouse=True)
def fresh_db():
    seed.init_db()
    from app.db import connect
    c = connect()
    c.execute("DELETE FROM calc_runs")
    c.commit()
    c.close()
    yield


def test_save_inserts_and_returns_id():
    out = estimate_writer.save_estimate(1, 1.15, "cross", note="ok")
    assert isinstance(out["run_id"], int) and out["run_id"] > 0
    assert out["paper_m2"] == 0.31
    assert out["ribbon_m"] == 2.2

    row = history.get_run(out["run_id"])
    assert row is not None
    assert row["paper_m2"] == out["paper_m2"]
    assert row["ribbon_m"] == out["ribbon_m"]
    assert row["wrap_style"] == "cross"
    assert row["overlap"] == 1.15
    assert row["box_name"] == "书型盒"
    # JSON 里也留着同一份数字
    assert row["result"]["paper_m2"] == out["paper_m2"]
    assert row["result"]["ribbon"]["ribbon_m"] == out["ribbon_m"]


def test_dirty_box_rejected_and_not_written():
    # id=3 是 seed 自带的脏盒（负高，data_quality=dirty）
    with pytest.raises(DirtyBox):
        estimate_writer.save_estimate(3, 1.15, "cross")
    assert history.list_runs() == []


def test_missing_box_rejected():
    with pytest.raises(BoxNotFound):
        estimate_writer.save_estimate(999, 1.15, "cross")
    assert history.list_runs() == []


def test_preview_does_not_write():
    out = estimate_writer.preview_estimate(1, 1.15, "cross")
    assert "run_id" not in out
    assert history.list_runs() == []


@pytest.mark.parametrize("style", ["cross", "band"])
def test_preview_save_readback_list_share_one_set_of_numbers(style):
    # 同一礼盒、同一 overlap、同一捆扎
    preview = estimate_writer.preview_estimate(2, 1.20, style)
    saved = estimate_writer.save_estimate(2, 1.20, style, note="n")
    detail = history.get_run(saved["run_id"])
    summary = next(r for r in history.list_runs() if r["id"] == saved["run_id"])

    # 与不触库的纯内核结果对齐，确认写入库与试算共用同一数字来源
    box = estimate_writer._load_clean_box(2)
    expected = estimate_core(box["length"], box["width"], box["height"], 1.20, style)

    for view, label in ((preview, "试算"), (saved, "落档响应"),
                        (detail, "编号读回"), (summary, "列表摘要")):
        assert view["paper_m2"] == expected["paper_m2"], label
        assert view["ribbon_m"] == expected["ribbon_m"], label

    assert preview["paper_m2"] == detail["paper_m2"] == summary["paper_m2"]
    assert preview["ribbon_m"] == detail["ribbon_m"] == summary["ribbon_m"]
    assert detail["wrap_style"] == summary["wrap_style"] == style


def test_default_overlap_comes_from_settings():
    out = estimate_writer.save_estimate(1, None, "cross")
    row = history.get_run(out["run_id"])
    assert row["overlap"] == 1.15
