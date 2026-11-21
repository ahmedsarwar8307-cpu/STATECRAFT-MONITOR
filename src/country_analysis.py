
import sqlite3
import pandas as pd

from pathlib import Path


# --------------------------------
# 1. CONNECT TO DATABASE
# --------------------------------

project_folder = Path(__file__).resolve().parent.parent

database_file = project_folder / "database" / "geointel.db"

connection = sqlite3.connect(database_file)


# --------------------------------
# 2. LOAD COUNTRY DATA
# --------------------------------

print("\nLoading country data...")

df = pd.read_sql_query(
    "SELECT countries FROM articles",
    connection
)

print(f"Articles loaded: {len(df)}")


# --------------------------------
# 3. SPLIT COUNTRY NAMES
# --------------------------------

df["countries"] = (
    df["countries"]
    .fillna("")
    .str.split(",")
)


# --------------------------------
# 4. EXPLODE COUNTRY LISTS
# --------------------------------

country_df = df.explode("countries")

country_df["countries"] = (
    country_df["countries"].str.strip()
)


# --------------------------------
# 5. REMOVE UNKNOWN COUNTRIES
# --------------------------------

country_df = country_df[
    (country_df["countries"] != "") &
    (country_df["countries"] != "Unknown")
]


# --------------------------------
# 6. COUNT COUNTRY COVERAGE
# --------------------------------

country_counts = (
    country_df["countries"]
    .value_counts()
)


# --------------------------------
# 7. DISPLAY REPORT
# --------------------------------

print("\n========== GEOINTEL AI ==========")
print("       COUNTRY COVERAGE REPORT")
print("=================================")

print("\nArticles mentioning each country:\n")

print(country_counts.rename_axis("Country").to_string())

print("\n=================================")

connection.close()

print("\nDatabase connection closed.")
