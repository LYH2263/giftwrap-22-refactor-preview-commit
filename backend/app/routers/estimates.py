"""HTTP 处理器：只做参数绑定与错误映射，不含计算与 SQL。

GET  /estimate  试算入口（不落库）
POST /estimate  写入入口（校验后落档，返回编号）
"""
from fastapi import APIRouter, HTTPException, Query

from app.schemas.estimate import EstimateRequest
from app.services import estimate_writer
from app.services.estimate_writer import EstimateError

router = APIRouter()


def _dispatch(func, *args):
    try:
        return func(*args)
    except EstimateError as exc:
        raise HTTPException(exc.status_code, str(exc))


@router.get("/estimate")
def get_est(box_id: int = Query(...), overlap: float | None = None,
            wrap_style: str = "cross"):
    return _dispatch(estimate_writer.preview_estimate, box_id, overlap, wrap_style)


@router.post("/estimate")
def post_est(body: EstimateRequest):
    return _dispatch(estimate_writer.save_estimate,
                     body.box_id, body.overlap, body.wrap_style, body.note)
