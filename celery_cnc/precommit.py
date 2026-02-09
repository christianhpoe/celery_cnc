"""Run pre-commit hooks via the project environment."""

from __future__ import annotations

import shutil
import subprocess
import sys


def main() -> None:
    """Execute pre-commit with any forwarded arguments."""
    executable = shutil.which("pre-commit")
    if executable is None:
        sys.stderr.write("pre-commit is not installed.\n")
        raise SystemExit(1)
    result = subprocess.run([executable, *sys.argv[1:]], check=False)  # noqa: S603
    raise SystemExit(result.returncode)
