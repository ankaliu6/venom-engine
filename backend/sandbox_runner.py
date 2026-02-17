# backend/sandbox_runner.py
import os
import tempfile
import subprocess
import json
import shutil
import textwrap

# resource 只在类 Unix 系统可用。Termux 和 Render 都支持 resource。
try:
    import resource
except Exception:
    resource = None

def _write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def make_test_runner(skill_filename, tests):
    """
    生成一个独立的 test_runner.py，负责导入 skill.py 并对 tests 逐条调用 run()
    tests: list of {"input": {...}, "expected": {...}} 或测试函数返回布尔
    """
    tests_json = json.dumps(tests, ensure_ascii=False)
    runner = f'''
import json,sys,traceback
tests = json.loads(r"""{tests_json}""")
try:
    import {os.path.splitext(os.path.basename(skill_filename))[0]} as skill
except Exception:
    traceback.print_exc()
    sys.exit(2)

results = []
for t in tests:
    inp = t.get("input", None)
    expected = t.get("expected", None)
    try:
        out = skill.run(inp) if hasattr(skill, "run") else None
        ok = (out == expected) if expected is not None else True
        results.append({{"ok": bool(ok), "input": inp, "output": out, "expected": expected}})
    except Exception as e:
        results.append({{"ok": False, "error": str(e), "traceback": traceback.format_exc()}})
# 输出 JSON，供外部解析
print(json.dumps({{"results": results}}, ensure_ascii=False))
'''
    return runner

def run_in_sandbox(code_text: str, tests: list, timeout: int = 8, mem_mb: int = 128):
    """
    code_text : 用户上传的 skill.py 内容（字符串）
    tests : 列表，每项 {"input": ..., "expected": ...}
    返回：{ ok: bool, score: float, details: {...}, stdout, stderr }
    """
    tmpdir = tempfile.mkdtemp(prefix="skill_")
    try:
        skill_path = os.path.join(tmpdir, "skill.py")
        _write_file(skill_path, code_text)

        # 生成 test_runner
        runner_path = os.path.join(tmpdir, "test_runner.py")
        _write_file(runner_path, make_test_runner(skill_path, tests))

        # 执行 test_runner.py，受限资源
        def preexec():
            # 设置 CPU time limit（秒）
            if resource:
                try:
                    resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
                except Exception:
                    pass
                # 内存限制（地址空间）
                try:
                    mem_bytes = mem_mb * 1024 * 1024
                    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
                except Exception:
                    pass

        proc = subprocess.run(
            ["python3", runner_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout+2,
            cwd=tmpdir,
            preexec_fn=preexec if resource else None
        )
        stdout = proc.stdout.decode(errors="replace")
        stderr = proc.stderr.decode(errors="replace")
        ok = proc.returncode == 0 or proc.returncode == 0
        # 尝试解析 stdout 为 JSON（results）
        details = {}
        try:
            parsed = json.loads(stdout.strip() or "{}")
            details = parsed
            # 计算 score: 每个测试 ok 得 1 分
            reslist = parsed.get("results", [])
            passed = sum(1 for r in reslist if r.get("ok"))
            total = len(reslist)
            score = round((passed / total) * 100, 2) if total>0 else 0.0
        except Exception:
            score = 0.0
            details = {"raw_stdout": stdout, "raw_stderr": stderr}

        return {"ok": True, "exit_code": proc.returncode, "score": score, "details": details, "stdout": stdout, "stderr": stderr}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "stdout": "", "stderr": "timeout"}
    except MemoryError:
        return {"ok": False, "error": "memory", "stdout": "", "stderr": "memory error"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass



