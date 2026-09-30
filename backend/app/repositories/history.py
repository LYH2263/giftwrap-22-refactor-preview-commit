import json
from datetime import datetime, timezone
from app.db import connect


def _column_exists(cur, table, column):
    rows = cur.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _ensure_columns(c):
    """存量库补列：paper_m2 / ribbon_m / wrap_style 与 JSON 并存，主字段以列为准。"""
    cur = c.execute("PRAGMA table_info(calc_runs)").fetchall()
    existing = {r["name"] for r in cur}
    if not existing:
        return
    if "paper_m2" not in existing:
        c.execute("ALTER TABLE calc_runs ADD COLUMN paper_m2 REAL")
    if "ribbon_m" not in existing:
        c.execute("ALTER TABLE calc_runs ADD COLUMN ribbon_m REAL")
    if "wrap_style" not in existing:
        c.execute("ALTER TABLE calc_runs ADD COLUMN wrap_style TEXT")
    # 旧行只有 result_json：把数字回填到列，保证读回仍是同一组
    rows = c.execute(
        "SELECT id,result_json FROM calc_runs WHERE paper_m2 IS NULL"
    ).fetchall()
    for row in rows:
        data = json.loads(row["result_json"] or "{}")
        ribbon = data.get("ribbon") or {}
        c.execute(
            "UPDATE calc_runs SET paper_m2=?,ribbon_m=?,wrap_style=? WHERE id=?",
            (data.get("paper_m2"), ribbon.get("ribbon_m"),
             ribbon.get("wrap_style"), row["id"]),
        )
    c.commit()


def insert_run(box_id, overlap, result, note=""):
    """插入用纸档；主字段写独立列，完整结果另存 JSON。返回编号。"""
    ribbon = result.get("ribbon") or {}
    c = connect()
    try:
        _ensure_columns(c)
        cur = c.execute(
            """INSERT INTO calc_runs
               (box_id,overlap,paper_m2,ribbon_m,wrap_style,result_json,note,created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            (box_id, overlap, result.get("paper_m2"), ribbon.get("ribbon_m"),
             ribbon.get("wrap_style"),
             json.dumps(result, ensure_ascii=False), note,
             datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()


def _row_to_summary(row):
    d = dict(row)
    result = json.loads(d.pop("result_json") or "{}")
    d["result"] = result
    # 主字段一律以钉住的列为准（列表摘要与详情同源）
    d["paper_m2"] = d.get("paper_m2")
    d["ribbon_m"] = d.get("ribbon_m")
    d["wrap_style"] = d.get("wrap_style")
    return d


def list_runs(limit=50):
    c = connect()
    try:
        _ensure_columns(c)
        rows = c.execute(
            """SELECT r.*, b.name box_name FROM calc_runs r
               LEFT JOIN boxes b ON b.id=r.box_id
               ORDER BY r.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [_row_to_summary(r) for r in rows]
    finally:
        c.close()


def get_run(run_id):
    c = connect()
    try:
        _ensure_columns(c)
        row = c.execute(
            """SELECT r.*, b.name box_name FROM calc_runs r
               LEFT JOIN boxes b ON b.id=r.box_id WHERE r.id=?""",
            (run_id,),
        ).fetchone()
        return _row_to_summary(row) if row else None
    finally:
        c.close()
