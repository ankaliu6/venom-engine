# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time

# 现有后端逻辑模块
from backend.skill_manager import list_skills, add_skill
from backend.project_manager import list_projects, add_project
from backend.upgrade_manager import propose_upgrade
from backend.optimizer import suggest_for_project
from backend.audit import log
from backend.database import get_conn

# 新增的 skills API（上传 / 激活）
from backend.skills_api import router as skills_router

app = FastAPI(title="Venom SuperEngine - 原型 (backend)")

# 跨域（前端可直接访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 将 skills_api 的路由挂载到主应用
app.include_router(skills_router)


# ---------- Pydantic 请求体定义（保留并兼容原有接口） ----------
class SkillIn(BaseModel):
    name: str
    version: Optional[str] = "1.0.0"
    manifest: Optional[dict] = {}
    metadata: Optional[dict] = {}

class UpgradeIn(BaseModel):
    name: str
    new_version: Optional[str] = None
    manifest: Optional[dict] = {}
    metadata: Optional[dict] = {}
    notes: Optional[str] = None

class ProjectIn(BaseModel):
    name: str
    description: Optional[str] = ""
    required_skills: Optional[List[str]] = []

# ---------- 启动事件 ----------
@app.on_event("startup")
def startup_event():
    # 确保 DB 初始化并写一条启动审计
    get_conn().close()
    log("系统", "启动", {"ts": int(time.time())})

# ---------- 原有公开 API（兼容旧前端） ----------
@app.get("/skills")
def api_list_skills():
    """
    返回已激活的技能列表（来自 skills 表/目录）
    说明：技能的上传/激活接口在 /skills/upload 和 /skills/activate（由 skills_api.py 提供）
    """
    return list_skills()

@app.post("/skills")
def api_add_skill(si: SkillIn):
    return add_skill(si.name, si.version, manifest=si.manifest, metadata=si.metadata, actor="用户")

@app.post("/skills/upgrade")
def api_upgrade(u: UpgradeIn):
    # 兼容旧接口：路由继续存在但内部调用统一到 upgrade_manager
    return propose_upgrade(u.name, {"new_version": u.new_version or f"auto-{int(time.time())}", "manifest": u.manifest, "metadata": u.metadata, "notes": u.notes}, actor="用户")

@app.get("/projects")
def api_list_projects():
    return list_projects()

@app.post("/projects")
def api_add_project(pi: ProjectIn):
    return add_project(pi.name, pi.description, required_skills=pi.required_skills, actor="用户")

@app.get("/optimizer/{project_id}")
def api_optimizer(project_id: int):
    return suggest_for_project(project_id)

@app.get("/audit")
def api_audit():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audits ORDER BY id DESC LIMIT 200")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.post("/simulate_task")
def api_simulate(skill_name: str):
    # 简单模拟：技能存在则成功
    skills = [s["name"] for s in list_skills()]
    ok = skill_name in skills
    log("simulator", "simulate", {"skill": skill_name, "result": ok})
    return {"skill": skill_name, "ok": ok}

# ---------- 根路由（简单健康检查） ----------
@app.get("/")
def root():
    return {"status": "ok", "message": "Venom SuperEngine backend running"}
