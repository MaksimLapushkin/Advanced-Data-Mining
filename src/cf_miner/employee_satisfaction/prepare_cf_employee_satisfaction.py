from pathlib import Path
import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]

INPUT_CSV = PROJECT_ROOT / "resources" / "ai_company_adoption.csv"
OUT_DIR = PROJECT_ROOT / "out" / "cf_miner"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUT_DIR / "prepared_cf_employee_satisfaction.csv"

ORD3 = ["1_low", "2_medium", "3_high"]


def to_ord3(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    out = pd.Series(index=series.index, dtype="object")

    valid_mask = s.notna()
    x = s.loc[valid_mask]

    if x.empty:
        return out

    try:
        binned = pd.qcut(x, q=3, labels=ORD3, duplicates="drop")
        if binned.nunique(dropna=True) < 3:
            raise ValueError("qcut produced fewer than 3 bins")
        out.loc[valid_mask] = binned.astype(str)
    except Exception:
        pct = x.rank(method="average", pct=True)
        out.loc[valid_mask] = np.where(
            pct <= 1 / 3,
            ORD3[0],
            np.where(pct <= 2 / 3, ORD3[1], ORD3[2]),
        )

    return out


def normalize_ethics_committee(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()

    yes_values = {"yes", "y", "true", "1", "present"}
    no_values = {"no", "n", "false", "0", "absent"}

    return s.map(
        lambda x: "HasCommittee" if x in yes_values else ("NoCommittee" if x in no_values else np.nan)
    )


def main() -> None:
    print(f"INPUT_CSV = {INPUT_CSV}")
    print(f"OUTPUT_CSV = {OUTPUT_CSV}")

    df = pd.read_csv(INPUT_CSV)

    # 1. define automation context first
    df["task_automation_level_ord"] = to_ord3(df["task_automation_rate"])

    # 2. keep only firms with medium automation
    filtered = df[df["task_automation_level_ord"] == "2_medium"].copy()

    # 3. build ordered target inside the filtered subset
    filtered["employee_satisfaction_ord"] = to_ord3(filtered["employee_satisfaction_score"])

    # 4. governance variables
    filtered["regulatory_compliance_ord"] = to_ord3(filtered["regulatory_compliance_score"])
    filtered["ai_ethics_committee_bin"] = normalize_ethics_committee(filtered["ai_ethics_committee"])
    filtered["ai_risk_management_ord"] = to_ord3(filtered["ai_risk_management_score"])

    # 5. workforce adaptation variables
    filtered["ai_training_hours_ord"] = to_ord3(filtered["ai_training_hours"])
    filtered["reskilled_employees_ord"] = to_ord3(filtered["reskilled_employees"])

    # 6. adoption intensity variables
    filtered["ai_adoption_rate_ord"] = to_ord3(filtered["ai_adoption_rate"])
    filtered["ai_projects_active_ord"] = to_ord3(filtered["ai_projects_active"])

    final_cols = [
        "regulatory_compliance_ord",
        "ai_ethics_committee_bin",
        "ai_risk_management_ord",
        "ai_training_hours_ord",
        "reskilled_employees_ord",
        "ai_adoption_rate_ord",
        "ai_projects_active_ord",
        "employee_satisfaction_ord",
    ]

    final_df = filtered[final_cols].dropna().astype(str)

    print("Prepared shape:", final_df.shape)
    print("\nTarget distribution:")
    print(final_df["employee_satisfaction_ord"].value_counts(dropna=False).sort_index())

    final_df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()