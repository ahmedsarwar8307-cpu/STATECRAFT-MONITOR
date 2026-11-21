
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
# 2. LOAD TOPIC DATA
# --------------------------------

print("\nLoading topic data...")

df = pd.read_sql_query(
    "SELECT topics FROM articles",
    connection
)

print(f"Articles loaded: {len(df)}")


# --------------------------------
# 3. SPLIT TOPIC NAMES
# --------------------------------

df["topics"] = (
    df["topics"]
    .fillna("")
    .str.split(",")
)


# --------------------------------
# 4. EXPLODE TOPIC LISTS
# --------------------------------

topic_df = df.explode("topics")

topic_df["topics"] = (
    topic_df["topics"].str.strip()
)


# --------------------------------
# 5. REMOVE EMPTY VALUES
# --------------------------------

topic_df = topic_df[
    (topic_df["topics"] != "") &
    (topic_df["topics"] != "Uncategorized")
]


# --------------------------------
# 6. COUNT TOPIC COVERAGE
# --------------------------------

topic_counts = (
    topic_df["topics"]
    .value_counts()
)


# --------------------------------
# 7. DISPLAY REPORT
# --------------------------------

print("\n========== GEOINTEL AI ==========")
print("        TOPIC COVERAGE REPORT")
print("=================================")

print("\nArticles by geopolitical topic:\n")

print(topic_counts.rename_axis("Topic").to_string())

print("\n=================================")

connection.close()

print("\nDatabase connection closed.")
