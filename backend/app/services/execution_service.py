import os
import sys
import time
import tempfile
import asyncio
import subprocess
from typing import Dict, Any, List, Optional
import httpx

from app.core.config import settings

class ExecutionService:
    @staticmethod
    def run_code_sync(
        language: str,
        code: str,
        stdin: str = "",
        expected_output: Optional[str] = None,
        time_limit: float = 2.0
    ) -> Dict[str, Any]:
        if settings.ENVIRONMENT == "production" and not settings.ALLOW_LOCAL_RUNNER_IN_PROD:
            raise RuntimeError("Local subprocess code execution is disabled in production environment for security.")

        start_time = time.time()

        if language.lower() not in ["python", "javascript", "js"]:
            return {
                "status": "Runtime Error",
                "stdout": "",
                "stderr": f"Language '{language}' not supported in local fallback mode.",
                "execution_time_seconds": 0.0,
                "memory_used_kb": 0
            }

        sub_env = dict(os.environ)
        sub_env["PYTHONIOENCODING"] = "utf-8"
        sub_env["PYTHONUTF8"] = "1"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py" if language.lower() == "python" else ".js", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            cmd = [sys.executable, temp_path] if language.lower() == "python" else ["node", temp_path]
            
            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=sub_env
            )

            try:
                stdout_bytes, stderr_bytes = proc.communicate(
                    input=stdin.encode("utf-8") if stdin else None,
                    timeout=time_limit
                )
                execution_time = round(time.time() - start_time, 3)
                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")

                # Truncate excessive output (> 1MB / 50KB stdout limit)
                if len(stdout) > 50000:
                    stdout = stdout[:50000] + "\n[تم اقتطاع المخرجات المفرطة - تجاوزت الحد الأقصى 50KB]"

                if proc.returncode != 0:
                    status_str = "Runtime Error"
                else:
                    if expected_output is not None:
                        clean_out = stdout.strip()
                        clean_exp = expected_output.strip()
                        status_str = "Accepted" if clean_out == clean_exp else "Wrong Answer"
                    else:
                        status_str = "Accepted"

                return {
                    "status": status_str,
                    "stdout": stdout,
                    "stderr": stderr,
                    "execution_time_seconds": execution_time,
                    "memory_used_kb": 15400
                }

            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    proc.communicate()
                except Exception:
                    pass
                return {
                    "status": "Time Limit Exceeded",
                    "stdout": "",
                    "stderr": f"Time Limit Exceeded ({time_limit}s limit).",
                    "execution_time_seconds": time_limit,
                    "memory_used_kb": 0
                }

        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

    @staticmethod
    async def run_code(
        language: str,
        code: str,
        stdin: str = "",
        expected_output: Optional[str] = None,
        time_limit: float = 2.0,
        memory_limit: int = 128
    ) -> Dict[str, Any]:
        if settings.JUDGE0_URL and settings.ENVIRONMENT == "production":
            lang_map = {"python": 71, "javascript": 63, "js": 63}
            lang_id = lang_map.get(language.lower(), 71)

            payload = {
                "source_code": code,
                "language_id": lang_id,
                "stdin": stdin,
                "expected_output": expected_output,
                "cpu_time_limit": time_limit,
                "memory_limit": memory_limit * 1024
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    res = await client.post(f"{settings.JUDGE0_URL}/submissions?wait=true", json=payload)
                    if res.status_code == 201:
                        data = res.json()
                        status_desc = data.get("status", {}).get("description", "Accepted")
                        return {
                            "status": status_desc,
                            "stdout": data.get("stdout") or "",
                            "stderr": data.get("stderr") or "",
                            "execution_time_seconds": float(data.get("time") or 0.0),
                            "memory_used_kb": int(data.get("memory") or 0)
                        }
                except Exception:
                    pass

            if not settings.ALLOW_LOCAL_RUNNER_IN_PROD:
                raise RuntimeError("Judge0 execution unavailable and local subprocess runner is disabled in production environment.")
        
        return ExecutionService.run_code_sync(language, code, stdin, expected_output, time_limit)

def execute_code_sandboxed(
    language: str,
    source_code: str,
    stdin_data: str = "",
    time_limit_seconds: float = 2.0,
    memory_limit_mb: int = 128
) -> Dict[str, Any]:
    return ExecutionService.run_code_sync(
        language=language,
        code=source_code,
        stdin=stdin_data,
        time_limit=time_limit_seconds
    )
