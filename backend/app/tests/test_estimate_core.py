"""试算核测例：全程在进程内纯内存运行。

不打开、不连接、不写入 SQLite，也不依赖任何事先插好的行；
另用一条元测例保证试算核源码里确实没有数据库/写回路径。
"""
import inspect

import app.services.estimate_core as core_mod
from app.services.estimate_core import PRIMARY_FIELDS, estimate_core


def test_book_box_matches_wrap_math():
    r = estimate_core(0.30, 0.20, 0.15, 1.15, "cross")
    # wrap_math: surface 0.27 * 1.15 = 0.3105 -> 0.31
    assert r["paper_m2"] == 0.31
    assert r["overlap"] == 1.15
    assert r["wrap_style"] == "cross"
    # cross: 2*2*(W+H) + L + 0.5 = 4*0.35 + 0.3 + 0.5 = 2.2
    assert r["ribbon_m"] == 2.2
    assert set(PRIMARY_FIELDS) == {"paper_m2", "ribbon_m"}
    assert set(["paper_m2", "ribbon_m"]) <= set(r)


def test_band_style_ribbon():
    r = estimate_core(0.30, 0.20, 0.15, 1.15, "band")
    # band: 2*(W+H) + 0.3 = 0.7 + 0.3 = 1.0
    assert r["ribbon_m"] == 1.0
    assert r["wrap_style"] == "band"
    assert r["paper_m2"] == 0.31


def test_unit_box_overlap_one():
    r = estimate_core(1, 1, 1, 1.0)
    assert r["paper_m2"] == 6.0
    assert r["ribbon_m"] > 0


def test_core_has_no_sqlite_or_session_write():
    """禁止把插入语句或 session 写回放进试算核。"""
    src = inspect.getsource(core_mod)
    forbidden = ("sqlite", "connect", "session", "insert", "commit",
                 "app.db", "repositories")
    lowered = src.lower()
    for token in forbidden:
        assert token not in lowered, f"试算核不得出现 {token!r}"
