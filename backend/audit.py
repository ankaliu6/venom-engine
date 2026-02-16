import time
from backend.database import get_conn
import json

def log(actor: str, action: str, details: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO audits (ts, actor, action, details) VALUES (?, ?, ?, ?)",
        (int(time.time()), actor, action, json.dumps(details, ensure_ascii=False))
    )
    conn.commit()
    conn.close()