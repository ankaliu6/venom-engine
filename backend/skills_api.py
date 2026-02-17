# backend/skills_api.py
import os
import time
import hashlib
import json
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from backend.audit import log
from backend.sandbox_runner import run_in_sandbox

router = APIRouter()

SKILLS_UPLOAD_DIR = "backend/uploads"
SKILLS_DIR = "backend/skills"

os.makedirs(SKILLS_UPLOAD_DIR, exist_ok=True)
os.makedirs(SKILLS_DIR, exist_ok=True)

class UploadPayload(BaseModel):
    name: str
    version: str = "0.0.1"
    code: str          # 整个 skill.py 源码文本
    tests: list = []   # list of {"input":..., "expected":...}

@router.post("/skills/upload")
def skills_upload(payload: UploadPayload):
    """
    上传 skill 源码并在 sandbox 中自动测试
    返回：{ passed: bool, score: float, details: {...} }
    """
    timestamp = int(time.time())
    safe_name = payload.name.replace(" ", "_")
    fname = f"{safe_name}_{timestamp}.py"
    upload_path = os.path.join(SKILLS_UPLOAD_DIR, fname)
    with open(upload_path, "w", encoding="utf-8") as f:
        f.write(payload.code)

    # run tests in sandbox
    result = run_in_sandbox(payload.code, payload.tests, timeout=8, mem_mb=128)

    # 记录审计
    log("user", "upload_skill", {"name": payload.name, "version": payload.version, "upload_file": upload_path, "result": result})
    return {"upload_file": upload_path, "result": result}

class ActivatePayload(BaseModel):
    name: str
    version: str
    source_upload_path: str  # 从 upload 接口返回的路径
    force: bool = False

@router.post("/skills/activate")
def skills_activate(payload: ActivatePayload):
    """
    激活 skill：把通过测试的上传文件移动到 skills/ 下并生成 metadata
    """
    src = payload.source_upload_path
    if not os.path.exists(src):
        raise HTTPException(status_code=400, detail="upload file not found")

    # 读取代码并计算 hash
    with open(src, "r", encoding="utf-8") as f:
        code = f.read()

    # 校验：可以在这里再次运行测试 或检查激活权限
    # 简单安全检查：文件不能包含 '__import__' 或 'os.system' 等危险调用（非常保守）
    unsafe_tokens = ["__import__", "os.system", "subprocess", "open(", "eval(", "exec("]
    for t in unsafe_tokens:
        if t in code:
            raise HTTPException(status_code=400, detail=f"包含不允许的代码片段: {t}")

    h = hashlib.sha256(code.encode("utf-8")).hexdigest()[:16]
    safe_dir = os.path.join(SKILLS_DIR, payload.name)
    os.makedirs(safe_dir, exist_ok=True)
    dest = os.path.join(safe_dir, f"{payload.name}_v{payload.version}_{h}.py")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(code)

    # 写 metadata
    meta = {
        "name": payload.name,
        "version": payload.version,
        "hash": h,
        "activated_at": int(time.time()),
    }
    with open(os.path.join(safe_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    log("user", "activate_skill", {"name": payload.name, "version": payload.version, "dest": dest})
    return {"activated": True, "path": dest, "meta": meta}
