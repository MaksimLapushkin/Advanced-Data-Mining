import os
import pandas as pd

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

INPUT_PATH = os.path.join(PROJECT_ROOT, "resources", "ai_company_adoption.csv")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "out", "four_ft_miner")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "prepared_enterprise_vs_startup.csv")

print("INPUT PATH:", INPUT_PATH)
print("INPUT EXISTS:", os.path.exists(INPUT_PATH))

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(INPUT_PATH)
print("Loaded shape:", df.shape)

# =========================
# KEEP ONLY ENTERPRISE AND STARTUP
# =========================
df = df[df["company_size"].isin(["Enterprise", "Startup"])].copy()

# =========================
# KEEP ONLY RELEVANT COLUMNS
# =========================
df = df[
    [
        "company_size",
        "ai_adoption_stage",
        "years_using_ai",
        "num_ai_tools_used",
        "ai_projects_active",
        "ai_training_hours",
        "ai_budget_percentage",
        "ai_maturity_score",
        "regulatory_compliance_score",
        "ai_risk_management_score",
        "task_automation_rate",
        "data_privacy_level",
        "ai_ethics_committee",
    ]
].copy()

# =========================
# DROP MISSING
# =========================
df = df.dropna().copy()

# =========================
# CREATE TARGET
# =========================
df["is_enterprise"] = df["company_size"] == "Enterprise"

# =========================
# QUANTILE BINNING
# =========================
def quantile_bin(series, labels=("low", "medium", "high")):
    ranked = series.rank(method="first")
    return pd.qcut(ranked, q=len(labels), labels=labels)

df["experience_level"] = quantile_bin(df["years_using_ai"])
df["tools_used_level"] = quantile_bin(df["num_ai_tools_used"])
df["projects_level"] = quantile_bin(df["ai_projects_active"])
df["training_level"] = quantile_bin(df["ai_training_hours"])
df["budget_level"] = quantile_bin(df["ai_budget_percentage"])
df["maturity_level"] = quantile_bin(df["ai_maturity_score"])
df["compliance_level"] = quantile_bin(df["regulatory_compliance_score"])
df["risk_level"] = quantile_bin(df["ai_risk_management_score"])
df["automation_level"] = quantile_bin(df["task_automation_rate"])

# =========================
# FINAL DATASET FOR 4FT
# =========================
df_final = df[
    [
        "ai_adoption_stage",
        "data_privacy_level",
        "ai_ethics_committee",
        "experience_level",
        "tools_used_level",
        "projects_level",
        "training_level",
        "budget_level",
        "maturity_level",
        "compliance_level",
        "risk_level",
        "automation_level",
        "is_enterprise",
    ]
].copy()

# =========================
# CONVERT TO STRING
# =========================
for col in df_final.columns:
    df_final[col] = df_final[col].astype(str)

# =========================
# SAVE
# =========================
df_final.to_csv(OUTPUT_PATH, index=False)

print("Prepared dataset saved to:")
print(OUTPUT_PATH)
print(df_final.head())
print(df_final.dtypes)
print("Final shape:", df_final.shape)