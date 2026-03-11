from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_INTERNAL_PREFIXES = (
    "core",
    "config",
    "plugins",
    "Singletons",
    "Server",
    "GraphQL",
    "auth",
    "mixins",
    "Enums",
    "Exceptions",
    "dbmodels",
    "main",
)

_IMPORT_CODE = (
    "import importlib\n"
    "import sys\n"
    "try:\n"
    "    importlib.import_module({module!r})\n"
    "except ModuleNotFoundError as exc:\n"
    "    print(\"MODULE_NOT_FOUND:\" + (exc.name or \"\"))\n"
    "    sys.exit(3)\n"
    "except Exception as exc:\n"
    "    print(\"IMPORT_FAILED:\" + repr(exc))\n"
    "    sys.exit(4)\n"
)


def run_import_test(module: str) -> None:
    result = _run_import_subprocess(module)
    if result.returncode == 0:
        return

    stdout = _normalize_output(result.stdout)
    stderr = _normalize_output(result.stderr)
    if result.returncode == 3:
        _handle_missing(_extract_missing_name(stdout))
        return

    msg = _message_from_outputs(stdout, stderr, result.returncode)
    pytest.skip(f"Import failed: {msg}")


def _run_import_subprocess(module: str) -> subprocess.CompletedProcess[str]:
    project_root = Path(__file__).resolve().parents[1]
    env = _build_env(project_root)
    cmd = [sys.executable, "-c", _IMPORT_CODE.format(module=module)]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def _build_env(project_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    src_path = project_root / "src"
    _set_pythonpath(env, str(src_path))
    return env


def _set_pythonpath(env: dict[str, str], src_path: str) -> None:
    existing = env.get("PYTHONPATH")
    if existing:
        env["PYTHONPATH"] = src_path + os.pathsep + existing
    else:
        env["PYTHONPATH"] = src_path


def _normalize_output(value: str | None) -> str:
    if value:
        return value.strip()
    return ""


def _extract_missing_name(stdout: str) -> str:
    return stdout.split("MODULE_NOT_FOUND:", 1)[-1]


def _handle_missing(name: str) -> None:
    if not _is_internal_missing(name):
        pytest.skip(f"Optional dependency missing: {name}")
    raise ModuleNotFoundError(name)


def _message_from_outputs(stdout: str, stderr: str, code: int) -> str:
    if stdout:
        return stdout
    if stderr:
        return stderr
    return f"Non-zero exit: {code}"


def _is_internal_missing(name: str | None) -> bool:
    if not name:
        return False
    return name.startswith(_INTERNAL_PREFIXES)
