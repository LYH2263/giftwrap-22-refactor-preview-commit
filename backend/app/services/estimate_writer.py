"""落档写入器：校验 → 调试算核 → 插入用纸档 → 返回编号。

试算（preview）与落档（save）共用同一颗试算核，只在最后一步分叉：
preview 直接返回数字，save 把同一组数字交给仓储插入并返回编号。
本模块不写任何 SQL，插入动作只在 repositories 层发生。
"""
from app.repositories import boxes, history, settings_repo
from app.services.estimate_core import estimate_core


class EstimateError(Exception):
    """算纸业务错误，HTTP 层据此映射状态码。"""
    status_code = 422


class BoxNotFound(EstimateError):
    status_code = 404


class DirtyBox(EstimateError):
    status_code = 422


def _load_clean_box(box_id: int) -> dict:
    box = boxes.get_box(box_id)
    if not box:
        raise BoxNotFound(f"box {box_id} not found")
    if box.get("data_quality") == "dirty":
        raise DirtyBox("dirty box")
    return box


def _prepare(box_id: int, overlap: float | None, wrap_style: str) -> tuple[dict, float, dict]:
    box = _load_clean_box(box_id)
    ov = float(overlap) if overlap is not None else settings_repo.get_overlap()
    calc = estimate_core(box["length"], box["width"], box["height"], ov, wrap_style)
    return box, ov, calc


def _ribbon_view(calc: dict) -> dict:
    return {"wrap_style": calc["wrap_style"], "ribbon_m": calc["ribbon_m"]}


def preview_estimate(box_id: int, overlap: float | None, wrap_style: str) -> dict:
    """试算入口：不落库，只返回钉版数字。"""
    box, _ov, calc = _prepare(box_id, overlap, wrap_style)
    return {"box": box, "ribbon": _ribbon_view(calc), **calc}


def save_estimate(box_id: int, overlap: float | None, wrap_style: str, note: str = "") -> dict:
    """写入入口：校验通过后插入用纸档，返回编号与同一组数字。"""
    box, ov, calc = _prepare(box_id, overlap, wrap_style)
    payload = {
        "paper_m2": calc["paper_m2"],
        "ribbon_m": calc["ribbon_m"],
        "wrap_style": calc["wrap_style"],
        "overlap": calc["overlap"],
        "ribbon": _ribbon_view(calc),
        "box_id": box_id,
    }
    run_id = history.insert_run(box_id, ov, payload, note)
    return {"box": box, "run_id": run_id, "ribbon": _ribbon_view(calc), **calc}
