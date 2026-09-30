"""试算核配套测例：纯进程内计算。

不打开、不连接、不写入 SQLite，也不依赖任何事先插好的脏行——
盒数据就是内存里的普通 dict。
"""

import inspect
import sqlite3

from app.services import estimate_core

# 内存盒，不来自任何库
BOX = {"id": 1, "name": "书型盒", "length": 0.30, "width": 0.20, "height": 0.15, "data_quality": "clean"}


def test_estimate_numbers():
    r = estimate_core.estimate(BOX, 1.15, "cross")
    assert r["paper_m2"] == 0.31
    assert r["box_surface"] == 0.27
    assert r["overlap"] == 1.15
    assert r["ribbon"] == {"wrap_style": "cross", "ribbon_m": 2.2}


def test_estimate_is_deterministic():
    assert estimate_core.estimate(BOX, 1.2, "band") == estimate_core.estimate(BOX, 1.2, "band")


def test_estimate_never_touches_sqlite(monkeypatch):
    def boom(*args, **kwargs):
        raise AssertionError("试算核不得打开/连接/写入 SQLite")

    monkeypatch.setattr(sqlite3, "connect", boom)
    r = estimate_core.estimate(BOX, 1.15, "cross")
    assert r["paper_m2"] == 0.31


def test_core_module_has_no_persistence_code():
    src = inspect.getsource(estimate_core)
    for token in ("INSERT", "sqlite3", "connect(", "execute(", "session"):
        assert token not in src
