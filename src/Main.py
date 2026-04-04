import pandas as pd

file_path = r"C:\Users\maxal\.cache\kagglehub\datasets\mohankrishnathalla\global-ai-adoption-and-workforce-impact-dataset\versions\1\ai_company_adoption.csv"

df = pd.read_csv(file_path)

small_df = df[["response_id", "company_size", "ai_adoption_stage"]].copy()

output_path = r"C:\Users\maxal\PycharmProjects\AdvancedDataMining\companysize_adoption_only.csv"
small_df.to_csv(output_path, index=False, encoding="utf-8-sig")

print("Saved to:", output_path)
print(small_df.head())
print(small_df.shape)