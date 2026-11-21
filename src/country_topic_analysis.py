
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
# 2. LOAD COUNTRY AND TOPIC DATA
# --------------------------------

print("\nLoading country and topic data...")

df = pd.read_sql_query(
    """
    SELECT id, title, countries, topics
    FROM articles
    """,
    connection
)

print(f"Articles loaded: {len(df)}")


# --------------------------------
# 3. SPLIT COUNTRY AND TOPIC NAMES
# --------------------------------

df["countries"] = (
    df["countries"]
    .fillna("")
    .str.split(",")
)

df["topics"] = (
    df["topics"]
    .fillna("")
    .str.split(",")
)


# --------------------------------
# 4. EXPLODE COUNTRIES
# --------------------------------

country_topic_df = df.explode("countries")

country_topic_df["countries"] = (
    country_topic_df["countries"].str.strip()
)


# --------------------------------
# 5. EXPLODE TOPICS
# --------------------------------

country_topic_df = country_topic_df.explode("topics")

country_topic_df["topics"] = (
    country_topic_df["topics"].str.strip()
)


# --------------------------------
# 6. REMOVE UNKNOWN AND EMPTY VALUES
# --------------------------------

country_topic_df = country_topic_df[
    (country_topic_df["countries"] != "") &
    (country_topic_df["countries"] != "Unknown") &
    (country_topic_df["topics"] != "") &
    (country_topic_df["topics"] != "Uncategorized")
].copy()


# --------------------------------
# 7. COUNT COUNTRY-TOPIC COMBINATIONS
# --------------------------------

country_topic_counts = (
    country_topic_df
    .groupby(["countries", "topics"])
    .size()
    .reset_index(name="article_count")
    .sort_values(
        by="article_count",
        ascending=False
    )
)


# --------------------------------
# 8. DISPLAY REPORT
# --------------------------------

print("\n========== GEOINTEL AI ==========")
print("  COUNTRY-TOPIC RELATIONSHIP REPORT")
print("=================================")

print("\nCountry and topic combinations:\n")

print(country_topic_counts.to_string(index=False))

print("\n=================================")

connection.close()

print("\nDatabase connection closed.")
