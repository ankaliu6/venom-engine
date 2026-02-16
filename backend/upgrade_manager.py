from backend.skill_manager import upgrade_skill
from backend.audit import log
import time

def propose_upgrade(skill_name: str, candidate_info: dict, actor="system"):
    new_ver = candidate_info.get("new_version", f"auto-{int(time.time())}")
    upgrade_skill(skill_name, new_ver, new_manifest=candidate_info.get("manifest"), new_metadata=candidate_info.get("metadata"), actor=actor)
    log(actor, "propose_upgrade", {"skill": skill_name, "new_version": new_ver, "notes": candidate_info.get("notes")})
    return {"skill": skill_name, "new_version": new_ver}