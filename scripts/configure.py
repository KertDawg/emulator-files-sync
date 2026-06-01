from __future__ import annotations

import platform
import shutil
import subprocess
import sys


def check_python() -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 or newer is required.")
    print(f"[ok] Python: {sys.version.split()[0]}")


def check_venv_module() -> None:
    try:
        import venv  # noqa: F401
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Python venv module is required.") from exc
    print("[ok] venv module available")


def check_make() -> None:
    if platform.system() == "Windows":
        print("[ok] Running on Windows; use make from Git Bash or WSL if needed.")
        return
    if shutil.which("make") is None:
        raise RuntimeError("GNU make is required.")
    print("[ok] make available")


def check_git() -> None:
    if shutil.which("git") is None:
        raise RuntimeError("git is required.")
    print("[ok] git available")


def main() -> int:
    try:
        check_python()
        check_venv_module()
        check_make()
        check_git()
        print("[ok] Configure checks passed")
        return 0
    except RuntimeError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
