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
def run_script(script_path: Path) -> None:
    print("\n" + "=" * 80)
    print(f"RUNNING: {script_path.name}")
    print("=" * 80)

    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    result = subprocess.run([sys.executable, str(script_path)])

    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path}")


# =========================
# SCRIPT PATHS
# =========================

# ---- enterprise vs startup ----
enterprise_prepare = (
    BASE_DIR
    / "four_ft_miner"
    / "enterprise_vs_startup"
    / "Prepare_enterprise_vs_startup_data.py"
)

enterprise_4ft = (
    BASE_DIR
    / "four_ft_miner"
    / "enterprise_vs_startup"
    / "four_ft_enterprise_vs_startup_data.py"
)

# ---- productivity ----
productivity_prepare = (
    BASE_DIR
    / "four_ft_miner"
    / "productivity"
    / "Prepare_high_productivity.py"
)

productivity_4ft = (
    BASE_DIR
    / "four_ft_miner"
    / "productivity"
    / "four_ft_high_productivity.py"
)

# ---- CF Miner: workforce balance ----
cf_wb_prepare = (
    BASE_DIR
    / "cf_miner"
    / "workforce_balance"
    / "prepare_cf_workforce_balance.py"
)

cf_wb_miner = (
    BASE_DIR
    / "cf_miner"
    / "workforce_balance"
    / "cf_workforce_balance.py"
)

# ---- CF Miner: employee satisfaction ----
cf_employee_satisfaction_prepare = (
    BASE_DIR
    / "cf_miner"
    / "employee_satisfaction"
    / "prepare_cf_employee_satisfaction.py"
)

cf_employee_satisfaction_miner = (
    BASE_DIR
    / "cf_miner"
    / "employee_satisfaction"
    / "cf_employee_satisfaction.py"
)


# =========================
# MAIN PIPELINE
# =========================
def main() -> None:
    # =====================
    # 4FT MINER
    # =====================

    # 1. Enterprise vs Startup
    run_script(enterprise_prepare)
    run_script(enterprise_4ft)

    # 2. High Productivity
    run_script(productivity_prepare)
    run_script(productivity_4ft)

    # =====================
    # CF MINER
    # =====================

    # 3. Workforce Balance
    run_script(cf_wb_prepare)
    run_script(cf_wb_miner)

    # 4. employee satisfaction
    run_script(cf_employee_satisfaction_prepare)
    run_script(cf_employee_satisfaction_miner)

    print("\n" + "=" * 80)
    print("ALL TASKS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()