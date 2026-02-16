import React, { useState } from "react";
import SkillList from "./components/SkillList.jsx";
import ProjectList from "./components/ProjectList.jsx";
import OptimizerPanel from "./components/OptimizerPanel.jsx";

function App(){
  const [view, setView] = useState("skills");
  const API_BASE = "";

  return (
    <div style={{padding:16}}>
      <h2>Venom SuperEngine - 中文原型</h2>
      <nav>
        <button onClick={()=>setView("skills")}>技能管理</button>
        <button onClick={()=>setView("projects")}>副业项目</button>
        <button onClick={()=>setView("opt")}>优化器</button>
      </nav>
      <div>
        {view==="skills" && <SkillList apiBase={API_BASE} />}
        {view==="projects" && <ProjectList apiBase={API_BASE} />}
        {view==="opt" && <OptimizerPanel apiBase={API_BASE} />}
      </div>
    </div>
  );
}
export default App;