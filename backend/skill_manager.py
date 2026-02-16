import time
import json
from backend.database import get_conn
from backend.audit import log

def list_skills():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM skills ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_skill(name: str, version: str = "1.0.0", manifest: dict = None, metadata: dict = None, actor="system"):
    manifest_json = json.dumps(manifest or {}, ensure_ascii=False)
    meta_json = json.dumps(metadata or {}, ensure_ascii=False)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO skills (name, version, manifest, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, version, manifest_json, meta_json, int(time.time())))
    conn.commit()
    conn.close()
    log(actor, "add_skill", {"name": name, "version": version})
    return {"name": name, "version": version}

def upgrade_skill(name: str, new_version: str, new_manifest: dict = None, new_metadata: dict = None, actor="system"):
    return add_skill(name, new_version, manifest=new_manifest, metadata=new_metadata, actor=actor)