import sqlite3
from pathlib import Path
from threading import Lock

DB_PATH = Path("venom_data.sqlite")
_db_lock = Lock()

def _ensure():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        version TEXT,
        manifest TEXT,
        metadata TEXT,
        created_at INTEGER
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        created_at INTEGER
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        skill_name TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS audits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts INTEGER,
        actor TEXT,
        action TEXT,
        details TEXT
    );
    """)
    conn.commit()
    conn.close()

def get_conn():
    _ensure()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn