"""试算核：由盒尺寸、重叠系数与捆扎方式纯算出用纸面积与丝带用量。

只产出 paper_m2 与 ribbon 等数值；不读库、不写库、不抛 HTTP 异常。
校验与落档归 estimate_writer，HTTP 归 routers.estimates。
"""

from app.engines.wrap_math import paper_area, ribbon_estimate


def estimate(box: dict, overlap: float, wrap_style: str = "cross") -> dict:
    """同一盒型、同一 overlap、同一捆扎，结果恒定。

    box 只需带 length/width/height 三个尺寸字段（普通 dict 即可）。
    """
    calc = paper_area(box["length"], box["width"], box["height"], float(overlap))
    ribbon = ribbon_estimate(box["length"], box["width"], box["height"], wrap_style)
    return {**calc, "ribbon": ribbon}
