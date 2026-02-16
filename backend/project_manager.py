import time
import json
from backend.database import get_conn
from backend.audit import log

def list_projects():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    for r in rows:
        cur2 = conn.cursor()
        cur2.execute("SELECT skill_name FROM project_skills WHERE project_id=?", (r["id"],))
        r["required_skills"] = [x["skill_name"] for x in cur2.fetchall()]
    conn.close()
    return rows

def add_project(name: str, description: str = "", required_skills: list = None, actor="system"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO projects (name, description, created_at) VALUES (?, ?, ?)",
                (name, description, int(time.time())))
    project_id = cur.lastrowid
    for s in (required_skills or []):
        cur.execute("INSERT INTO project_skills (project_id, skill_name) VALUES (?, ?)", (project_id, s))
    conn.commit()
    conn.close()
    log(actor, "add_project", {"name": name, "required_skills": required_skills or []})
    return {"id": project_id, "name": name}