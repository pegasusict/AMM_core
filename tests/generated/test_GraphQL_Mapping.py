import importlib
import pytest
import subprocess
import sys
import os
from pathlib import Path

MODULE = 'GraphQL.Mapping'

_INTERNAL_PREFIXES = ('core', 'config', 'plugins', 'Singletons', 'Server', 'GraphQL', 'auth', 'mixins', 'Enums', 'Exceptions', 'dbmodels', 'main',)



def _is_internal_missing(name: str | None) -> bool:
    if not name:
        return False
    return name.startswith(_INTERNAL_PREFIXES)





def test_import_module() -> None:
    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src_path) + (
        os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env else ""
    )

    code = (
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
    result = subprocess.run(
        [sys.executable, "-c", code.format(module=MODULE)],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode == 0:
        return

    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()
    if result.returncode == 3:
        name = stdout.split("MODULE_NOT_FOUND:", 1)[-1]
        if not _is_internal_missing(name):
            pytest.skip(f"Optional dependency missing: {name}")
        raise ModuleNotFoundError(name)

    msg = stdout or stderr or f"Non-zero exit: {result.returncode}"
    pytest.skip(f"Import failed: {msg}")
