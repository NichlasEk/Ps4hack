Import("env")
import runpy
from pathlib import Path

runpy.run_path(str(Path(env.subst("$PROJECT_DIR")) / "scripts/extract_assets.py"),
              run_name="__main__")
runpy.run_path(str(Path(env.subst("$PROJECT_DIR")) / "scripts/check_assets.py"),
              run_name="__main__")
