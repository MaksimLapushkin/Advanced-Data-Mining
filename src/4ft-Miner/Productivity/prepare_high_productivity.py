import os

import pandas as pd

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# корень проекта: AdvancedDataMining
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

# Путь к исходному файлу (у тебя уже есть)
file_path = os.path.join(PROJECT_ROOT, "resources", "ai_company_adoption.csv")
# Загружаем
df = pd.read_csv(file_path)

print("Loaded:", df.shape)

# Берем только нужные колонки
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
# СОЗДАЕМ TARGET (самое важное)
# ===============================

# high productivity = выше медианы
threshold = df["productivity_change_percent"].median()

df["high_productivity"] = df["productivity_change_percent"] > threshold

print("Threshold:", threshold)
print(df["high_productivity"].value_counts())

# ===============================
# ДИСКРЕТИЗАЦИЯ (обязательно для 4ft)
# ===============================

# Разбиваем числовые поля на категории (low / medium / high)

def bin_column(col, name):
    df[name] = pd.qcut(col, q=3, labels=["low", "medium", "high"])

bin_column(df["ai_maturity_score"], "ai_maturity")
bin_column(df["ai_training_hours"], "training_level")
bin_column(df["ai_projects_active"], "projects_level")
bin_column(df["ai_budget_percentage"], "budget_level")
bin_column(df["task_automation_rate"], "automation_level")

# ===============================
# ОСТАВЛЯЕМ ТОЛЬКО КАТЕГОРИИ
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
# СОХРАНЯЕМ
# ===============================

output_dir = os.path.join(PROJECT_ROOT, "out", "4ft-Miner")
os.makedirs(output_dir, exist_ok=True)

# выходной файл
output_path = os.path.join(output_dir, "high_productivity_4ft.csv")
df_final.to_csv(output_path, index=False)

print("Saved to:", output_path)
print(df_final.head())