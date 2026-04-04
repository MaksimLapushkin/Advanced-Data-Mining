import os
import pandas as pd

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

input_path = os.path.join(PROJECT_ROOT, "resources", "ai_company_adoption.csv")
output_dir = os.path.join(PROJECT_ROOT, "out", "4ft-Miner")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "prepared_ai_adoption.csv")

print("INPUT PATH:", input_path)
print("INPUT EXISTS:", os.path.exists(input_path))

# =========================
# LOAD
# =========================
df = pd.read_csv(input_path)

print("Loaded shape:", df.shape)

# =========================
# KEEP ONLY NEEDED COLUMNS
# =========================
df = df[[
    "industry",
    "company_size",
    "company_age_group",
    "ai_adoption_stage",
    "ai_projects_active",
    "ai_training_hours",
    "ai_budget_percentage",
    "ai_maturity_score",
    "task_automation_rate"
]].copy()

# =========================
# DROP MISSING
# =========================
df = df.dropna().copy()

# =========================
# TARGET
# =========================
df["ai_adoption_full"] = df["ai_adoption_stage"] == "full"

# =========================
# DISCRETIZATION
# =========================
def bin_column(series, labels=("low", "medium", "high")):
    return pd.qcut(series, q=3, labels=labels, duplicates="drop")

df["projects_level"] = bin_column(df["ai_projects_active"])
df["training_level"] = bin_column(df["ai_training_hours"])
df["budget_level"] = bin_column(df["ai_budget_percentage"])
df["maturity_level"] = bin_column(df["ai_maturity_score"])
df["automation_level"] = bin_column(df["task_automation_rate"])

# =========================
# FINAL DATASET FOR 4FT
# =========================
df_final = df[[
    "industry",
    "company_size",
    "company_age_group",
    "projects_level",
    "training_level",
    "budget_level",
    "maturity_level",
    "automation_level",
    "ai_adoption_full"
]].copy()

# всё в строки
for col in df_final.columns:
    df_final[col] = df_final[col].astype(str)

# =========================
# SAVE
# =========================
df_final.to_csv(output_path, index=False)

print("Prepared dataset saved to:")
print(output_path)
print(df_final.head())
print(df_final.dtypes)