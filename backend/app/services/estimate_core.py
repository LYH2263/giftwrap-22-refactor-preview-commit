"""试算核：纯计算，只产出 paper_m2 与 ribbon。

不导入数据库、仓储或框架相关模块，不打开连接，也不向任何会话写回；
同一份数字既供试算入口直接返回，也供落档写入器在写入前调用。
"""
from app.engines.wrap_math import paper_area, ribbon_estimate

# 与「用纸档」列表摘要、详情共同钉住的主字段
PRIMARY_FIELDS = ("paper_m2", "ribbon_m")


def estimate_core(length: float, width: float, height: float,
                  overlap: float, wrap_style: str = "cross") -> dict:
    """纯函数：输入盒子尺寸/overlap/捆扎，输出钉版数字。

    返回 {"paper_m2", "ribbon_m", "wrap_style", "overlap"}，
    不触碰数据库，不依赖任何预置行。
    """
    area = paper_area(length, width, height, overlap)
    ribbon = ribbon_estimate(length, width, height, wrap_style)
    return {
        "paper_m2": area["paper_m2"],
        "ribbon_m": ribbon["ribbon_m"],
        "wrap_style": ribbon["wrap_style"],
        "overlap": area["overlap"],
    }
