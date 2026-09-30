"""落档写入器：校验礼盒后，把试算核的结果写入用纸档并返回档号。

试算核（estimate_core）只算数、不碰库；写库只发生在本模块。
试算与落档共用同一内核，保证两条路径对外数字一致。
"""

from app.repositories import boxes, history, settings_repo
from app.services.estimate_core import estimate


class BoxNotFoundError(Exception):
    """礼盒不存在。"""


class DirtyBoxError(Exception):
    """礼盒数据为脏，禁止试算与落档。"""


def validate_box(box_id: int) -> dict:
    """取盒并校验：不存在抛 BoxNotFoundError，脏盒抛 DirtyBoxError。"""
    box = boxes.get_box(box_id)
    if not box:
        raise BoxNotFoundError(f"box {box_id} not found")
    if box.get("data_quality") == "dirty":
        raise DirtyBoxError(f"box {box_id} is dirty")
    return box


def resolve_overlap(overlap: float | None) -> float:
    """未显式给重叠系数时，回退到系统设置。"""
    return float(overlap) if overlap is not None else settings_repo.get_overlap()


def save_estimate(box_id: int, overlap: float | None = None, wrap_style: str = "cross", note: str = "") -> dict:
    """校验 -> 试算 -> 插入用纸档，返回带 run_id（档号）的结果。"""
    box = validate_box(box_id)
    ov = resolve_overlap(overlap)
    result = estimate(box, ov, wrap_style)
    run_id = history.insert_run(box_id, ov, {**result, "box_id": box_id}, note)
    return {"box": box, "run_id": run_id, **result}
