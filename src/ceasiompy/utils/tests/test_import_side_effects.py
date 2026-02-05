import os
import subprocess
import sys


def _run_python(code: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.run([sys.executable, "-c", code], env=env, check=False)


def test_print_not_redirected_by_default():
    code = """
import builtins
old = builtins.print
import ceasiompy
import builtins as b
raise SystemExit(0 if b.print is old else 1)
"""
    res = _run_python(code, {"CEASIOMPY_REDIRECT_PRINT": "0"})
    assert res.returncode == 0


def test_print_redirection_opt_in():
    code = """
import builtins
old = builtins.print
import ceasiompy
import builtins as b
raise SystemExit(0 if b.print is not old else 1)
"""
    res = _run_python(code, {"CEASIOMPY_REDIRECT_PRINT": "1"})
    assert res.returncode == 0


def test_utils_init_does_not_import_streamlit():
    code = """
import sys
import ceasiompy.utils
raise SystemExit(0 if 'streamlit' not in sys.modules else 1)
"""
    res = _run_python(code, {"CEASIOMPY_REDIRECT_PRINT": "0"})
    assert res.returncode == 0

