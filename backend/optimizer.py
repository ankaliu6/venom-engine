from backend.skill_manager import list_skills
from backend.project_manager import list_projects
from backend.audit import log

def suggest_for_project(project_id: int):
    projects = list_projects()
    proj = next((p for p in projects if p["id"] == project_id), None)
    if not proj:
        return {"error": "项目不存在"}
    available = [s["name"] for s in list_skills()]
    missing = [rs for rs in proj.get("required_skills", []) if rs not in available]
    suggestions = []
    if missing:
        for m in missing:
            suggestions.append({"type": "新增技能", "skill": m, "reason": "项目需要"})
    else:
        suggestions.append({"type": "技能组合", "plan": "使用本地技能形成流水线: " + ", ".join(proj.get("required_skills", []))})
    log("optimizer", "suggest", {"project_id": project_id, "missing": missing, "suggestions": suggestions})
    return {"project": proj, "suggestions": suggestions}