from fastapi import APIRouter, HTTPException, Query

from app.schemas.estimate import EstimateRequest
from app.services import estimate_core, estimate_writer

router = APIRouter()


def _trial(box_id: int, overlap: float | None, wrap_style: str) -> dict:
    """试算不落档：校验后只调试算核，run_id 恒为 None。"""
    box = estimate_writer.validate_box(box_id)
    ov = estimate_writer.resolve_overlap(overlap)
    return {"box": box, "run_id": None, **estimate_core.estimate(box, ov, wrap_style)}


def _run(box_id: int, overlap: float | None, wrap_style: str, save: bool, note: str) -> dict:
    try:
        if save:
            return estimate_writer.save_estimate(box_id, overlap, wrap_style, note)
        return _trial(box_id, overlap, wrap_style)
    except estimate_writer.BoxNotFoundError as exc:
        raise HTTPException(404) from exc
    except estimate_writer.DirtyBoxError as exc:
        raise HTTPException(422, "dirty box") from exc


@router.get("/estimate")
def get_est(box_id: int = Query(...), overlap: float | None = None, wrap_style: str = "cross", save: bool = False):
    return _run(box_id, overlap, wrap_style, save, "")


@router.post("/estimate")
def post_est(body: EstimateRequest):
    return _run(body.box_id, body.overlap, body.wrap_style, body.save, body.note)
