import json
from datetime import datetime, timezone
from app.db import connect

def insert_run(box_id, overlap, result, note=""):
    c = connect()
    try:
        cur = c.execute(
            "INSERT INTO calc_runs(box_id,overlap,result_json,note,created_at) VALUES (?,?,?,?,?)",
            (box_id, overlap, json.dumps(result, ensure_ascii=False), note, datetime.now(timezone.utc).isoformat()),
        )
        c.commit()
        return int(cur.lastrowid)
    finally:
        c.close()

def _decode(row):
    d = dict(row)
    d["result"] = json.loads(d.pop("result_json"))
    return d

def get_run(run_id):
    c = connect()
    try:
        r = c.execute(
            """SELECT r.*, b.name box_name FROM calc_runs r LEFT JOIN boxes b ON b.id=r.box_id WHERE r.id=?""",
            (run_id,),
        ).fetchone()
        return _decode(r) if r else None
    finally:
        c.close()

def list_runs(limit=50):
    c = connect()
    try:
        rows = c.execute(
            """SELECT r.*, b.name box_name FROM calc_runs r LEFT JOIN boxes b ON b.id=r.box_id ORDER BY r.id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [_decode(row) for row in rows]
    finally:
        c.close()
