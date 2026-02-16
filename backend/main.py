from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import time

from backend.skill_manager import list_skills, add_skill
from backend.project_manager import list_projects, add_project
from backend.upgrade_manager import propose_upgrade
from backend.optimizer import suggest_for_project
from backend.audit import log
from backend.database import get_conn

app = FastAPI(title="Venom SuperEngine - 原型")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.on_event("startup")
def startup_event():
    get_conn().close()
    log("system", "startup", {"ts": int(time.time())})

@app.get("/skills")
def api_list_skills():
    return list_skills()

@app.post("/skills")
def api_add_skill(si: SkillIn):
    return add_skill(si.name, si.version, manifest=si.manifest, metadata=si.metadata, actor="用户")

@app.post("/skills/upgrade")
def api_upgrade(u: UpgradeIn):
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