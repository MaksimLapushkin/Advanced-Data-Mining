import subprocess
import sys
from pathlib import Path

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent

# =========================
# HELPER
# =========================
def run_script(script_path):
    print(f"\n{'='*60}")
    print(f"RUNNING: {script_path.name}")
    print(f"{'='*60}")

    result = subprocess.run([sys.executable, str(script_path)])

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path}")

# =========================
# PIPELINE
# =========================

# ---- enterprise vs startup ----
enterprise_prepare = BASE_DIR / "4ft-Miner" / "enterprise_vs_startup" / "prepare_enterprise_vs_startup_data.py"
enterprise_4ft = BASE_DIR / "4ft-Miner" / "enterprise_vs_startup" / "4ft_enterprise_vs_startup_data.py"

# ---- productivity ----
productivity_prepare = BASE_DIR / "4ft-Miner" / "productivity" / "prepare_high_productivity.py"
productivity_4ft = BASE_DIR / "4ft-Miner" / "productivity" / "4ft_high_productivity.py"

# =========================
# RUN ORDER
# =========================

if __name__ == "__main__":

    # 1. Enterprise vs Startup
    run_script(enterprise_prepare)
    run_script(enterprise_4ft)

    # 2. Productivity
    run_script(productivity_prepare)
    run_script(productivity_4ft)

    print(f"\n{'='*60}")
    print("ALL TASKS COMPLETED")
    print(f"{'='*60}")