
import pandas as pd
from pathlib import Path


# --------------------------------
# 1. DEFINE PROJECT PATHS
# --------------------------------

project_folder = Path(__file__).resolve().parent.parent

raw_file = project_folder / "data" / "raw" / "news.csv"

processed_folder = project_folder / "data" / "processed"

processed_folder.mkdir(parents=True, exist_ok=True)

processed_file = processed_folder / "news_cleaned.csv"


# --------------------------------
# 2. LOAD RAW DATASET
# --------------------------------

print("\nLoading raw news dataset...")

df = pd.read_csv(raw_file)

print(f"Original records: {len(df)}")


# --------------------------------
# 3. CHECK REQUIRED COLUMNS
# --------------------------------

required_columns = ["source", "title", "published", "link"]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(f"Missing columns: {missing_columns}")


# --------------------------------
# 4. CLEAN TEXT FORMATTING
# --------------------------------

text_columns = ["source", "title", "published", "link"]

for column in text_columns:
    df[column] = df[column].fillna("").astype(str).str.strip()


# --------------------------------
# 5. REMOVE INVALID RECORDS
# --------------------------------

before_validation = len(df)

df = df[
    (df["source"] != "") &
    (df["title"] != "") &
    (df["link"] != "")
].copy()

invalid_removed = before_validation - len(df)


# --------------------------------
# 6. REMOVE DUPLICATE ARTICLES
# --------------------------------

before_duplicates = len(df)

df = df.drop_duplicates(subset=["link"]).copy()

duplicates_removed = before_duplicates - len(df)


# --------------------------------
# 7. SAVE CLEANED DATASET
# --------------------------------

df.to_csv(processed_file, index=False, encoding="utf-8-sig")


# --------------------------------
# 8. DISPLAY DATA QUALITY REPORT
# --------------------------------

print("\n========== GEOINTEL AI ==========")
print("       DATA QUALITY REPORT")
print("=================================")

print(f"Original records: {before_validation}")
print(f"Invalid records removed: {invalid_removed}")
print(f"Duplicate records removed: {duplicates_removed}")
print(f"Final clean records: {len(df)}")

print("\nArticles by source:")
print(df["source"].value_counts().to_string())

print(f"\nClean dataset saved at:\n{processed_file}")

print("\n=================================")
