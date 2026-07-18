"""Deploy the bundled CST runtime into this workspace."""
from pathlib import Path
import runpy

runpy.run_path(
    Path("skills/cst-runtime-cli/scripts/bootstrap.py").resolve().as_posix(),
    run_name="__main__",
)
