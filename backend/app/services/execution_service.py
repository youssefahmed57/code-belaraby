import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings


SUPPORTED_EXECUTION_LANGUAGES = {"python", "javascript", "js"}


class ExecutionProviderUnavailable(RuntimeError):
    pass


class UnsafeLocalExecutionDisabled(RuntimeError):
    pass


def _local_execution_allowed() -> bool:
    return settings.is_development_like() and settings.ALLOW_UNSAFE_LOCAL_CODE_EXECUTION


def _default_error_result(detail: str) -> Dict[str, Any]:
    return {
        "status": "Internal Error",
        "stdout": "",
        "stderr": detail,
        "execution_time_seconds": 0.0,
        "memory_used_kb": 0,
    }


class ExecutionService:
    @staticmethod
    def run_code_sync(
        language: str,
        code: str,
        stdin: str = "",
        expected_output: Optional[str] = None,
        time_limit: float = 2.0,
    ) -> Dict[str, Any]:
        if not _local_execution_allowed():
            raise UnsafeLocalExecutionDisabled(
                "Unsafe local code execution is disabled outside explicit development and test environments."
            )

        normalized_language = language.lower()
        if normalized_language not in SUPPORTED_EXECUTION_LANGUAGES:
            return _default_error_result(f"Language '{language}' is not supported.")

        start_time = time.time()
        temp_path = ""
        file_suffix = ".py" if normalized_language == "python" else ".js"
        command = [sys.executable, temp_path] if normalized_language == "python" else ["node", temp_path]
        safe_env = os.environ.copy()
        safe_env.update(
            {
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
                "HOME": tempfile.gettempdir(),
                "TEMP": tempfile.gettempdir(),
                "TMP": tempfile.gettempdir(),
                "LANG": os.environ.get("LANG", "C.UTF-8"),
            }
        )

        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=file_suffix, delete=False, encoding="utf-8") as handle:
                handle.write(code)
                temp_path = handle.name

            command[-1] = temp_path
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=safe_env,
                cwd=tempfile.gettempdir(),
            )
            try:
                stdout_bytes, stderr_bytes = process.communicate(
                    input=stdin.encode("utf-8") if stdin else None,
                    timeout=time_limit,
                )
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                return {
                    "status": "Time Limit Exceeded",
                    "stdout": "",
                    "stderr": f"Time limit exceeded ({time_limit}s).",
                    "execution_time_seconds": time_limit,
                    "memory_used_kb": 0,
                }

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            if len(stdout.encode("utf-8")) > settings.MAX_EXECUTION_OUTPUT_BYTES:
                truncated = stdout.encode("utf-8")[: settings.MAX_EXECUTION_OUTPUT_BYTES].decode("utf-8", errors="ignore")
                stdout = truncated + "\n[output truncated at 50KB]"

            if process.returncode != 0:
                status_text = "Runtime Error"
            elif expected_output is not None and stdout.strip() != expected_output.strip():
                status_text = "Wrong Answer"
            else:
                status_text = "Accepted"

            return {
                "status": status_text,
                "stdout": stdout,
                "stderr": stderr,
                "execution_time_seconds": round(time.time() - start_time, 3),
                "memory_used_kb": 0,
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    @staticmethod
    async def run_code_with_judge0(
        language: str,
        code: str,
        stdin: str = "",
        expected_output: Optional[str] = None,
        time_limit: float = 2.0,
        memory_limit: int = 128,
    ) -> Dict[str, Any]:
        if not settings.JUDGE0_URL:
            raise ExecutionProviderUnavailable("Judge0 is not configured.")

        language_map = {"python": 71, "javascript": 63, "js": 63}
        normalized_language = language.lower()
        if normalized_language not in language_map:
            return _default_error_result(f"Language '{language}' is not supported.")

        payload = {
            "source_code": code,
            "language_id": language_map[normalized_language],
            "stdin": stdin,
            "expected_output": expected_output,
            "cpu_time_limit": time_limit,
            "memory_limit": memory_limit * 1024,
            "number_of_runs": 1,
            "wall_time_limit": max(time_limit + 1.0, time_limit * 2),
            "enable_network": False,
        }

        headers = {}
        if settings.JUDGE0_API_KEY:
            headers["X-Auth-Token"] = settings.JUDGE0_API_KEY

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{settings.JUDGE0_URL.rstrip('/')}/submissions?wait=true",
                    json=payload,
                    headers=headers,
                )
        except Exception as exc:
            raise ExecutionProviderUnavailable("Judge0 is unavailable.") from exc

        if response.status_code != 201:
            raise ExecutionProviderUnavailable("Judge0 rejected the execution request.")

        data = response.json()
        return {
            "status": data.get("status", {}).get("description", "Internal Error"),
            "stdout": data.get("stdout") or "",
            "stderr": data.get("stderr") or data.get("compile_output") or "",
            "execution_time_seconds": float(data.get("time") or 0.0),
            "memory_used_kb": int(data.get("memory") or 0),
        }

    @staticmethod
    async def run_code(
        language: str,
        code: str,
        stdin: str = "",
        expected_output: Optional[str] = None,
        time_limit: float = 2.0,
        memory_limit: int = 128,
    ) -> Dict[str, Any]:
        if settings.JUDGE0_URL:
            try:
                return await ExecutionService.run_code_with_judge0(
                    language=language,
                    code=code,
                    stdin=stdin,
                    expected_output=expected_output,
                    time_limit=time_limit,
                    memory_limit=memory_limit,
                )
            except ExecutionProviderUnavailable:
                if settings.requires_isolated_code_execution():
                    raise

        if settings.requires_isolated_code_execution():
            raise ExecutionProviderUnavailable(
                "Isolated code execution is required in staging and production, and the configured sandbox is unavailable."
            )

        return ExecutionService.run_code_sync(
            language=language,
            code=code,
            stdin=stdin,
            expected_output=expected_output,
            time_limit=time_limit,
        )

    @staticmethod
    async def check_execution_provider_health() -> Dict[str, Any]:
        if not settings.JUDGE0_URL:
            return {"configured": False, "healthy": False, "provider": "judge0"}

        headers = {}
        if settings.JUDGE0_API_KEY:
            headers["X-Auth-Token"] = settings.JUDGE0_API_KEY

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.JUDGE0_URL.rstrip('/')}/languages", headers=headers)
            return {"configured": True, "healthy": response.status_code == 200, "provider": "judge0"}
        except Exception:
            return {"configured": True, "healthy": False, "provider": "judge0"}


async def execute_code_sandboxed(
    language: str,
    source_code: str,
    stdin_data: str = "",
    expected_output: Optional[str] = None,
    time_limit_seconds: float = 2.0,
    memory_limit_mb: int = 128,
) -> Dict[str, Any]:
    try:
        return await ExecutionService.run_code(
            language=language,
            code=source_code,
            stdin=stdin_data,
            expected_output=expected_output,
            time_limit=time_limit_seconds,
            memory_limit=memory_limit_mb,
        )
    except (ExecutionProviderUnavailable, UnsafeLocalExecutionDisabled):
        if settings.requires_isolated_code_execution():
            raise
        return _default_error_result("Code execution is currently unavailable.")
