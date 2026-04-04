import os
import pandas as pd

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root: AdvancedDataMining
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

# Path to the input file (already exists)
file_path = os.path.join(PROJECT_ROOT, "resources", "ai_company_adoption.csv")

# Load data
df = pd.read_csv(file_path)

print("Loaded:", df.shape)

# Select only relevant columns
df = df[[
    "industry",
    "company_size",
    "ai_adoption_stage",
    "ai_maturity_score",
    "ai_training_hours",
    "ai_projects_active",
    "ai_budget_percentage",
    "task_automation_rate",
    "productivity_change_percent"
]].copy()

print("Selected columns:", df.shape)

# ===============================
# CREATE TARGET VARIABLE (most important)
# ===============================

# High productivity = above median
threshold = df["productivity_change_percent"].median()

df["high_productivity"] = df["productivity_change_percent"] > threshold

print("Threshold:", threshold)
print(df["high_productivity"].value_counts())

# ===============================
# DISCRETIZATION (required for 4ft)
# ===============================

# Convert numerical features into categories (low / medium / high)
def bin_column(col, name):
    df[name] = pd.qcut(col, q=3, labels=["low", "medium", "high"])

bin_column(df["ai_maturity_score"], "ai_maturity")
bin_column(df["ai_training_hours"], "training_level")
bin_column(df["ai_projects_active"], "projects_level")
bin_column(df["ai_budget_percentage"], "budget_level")
bin_column(df["task_automation_rate"], "automation_level")

# ===============================
# KEEP ONLY CATEGORICAL FEATURES
# ===============================

df_final = df[[
    "industry",
    "company_size",
    "ai_adoption_stage",
    "ai_maturity",
    "training_level",
    "projects_level",
    "budget_level",
    "automation_level",
    "high_productivity"
]].copy()

# ===============================
# SAVE OUTPUT
# ===============================

output_dir = os.path.join(PROJECT_ROOT, "out", "four_ft_miner")
os.makedirs(output_dir, exist_ok=True)

# Output file
output_path = os.path.join(output_dir, "high_productivity_4ft.csv")
df_final.to_csv(output_path, index=False)

print("Saved to:", output_path)
print(df_final.head())