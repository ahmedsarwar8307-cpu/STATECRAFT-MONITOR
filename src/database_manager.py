
import sqlite3
import pandas as pd

from pathlib import Path


# --------------------------------
# 1. DEFINE PROJECT PATHS
# --------------------------------

project_folder = Path(__file__).resolve().parent.parent

input_file = (
    project_folder
    / "data"
    / "processed"
    / "news_with_topics.csv"
)

database_folder = project_folder / "database"
database_folder.mkdir(parents=True, exist_ok=True)

database_file = database_folder / "geointel.db"


# --------------------------------
# 2. LOAD CLASSIFIED NEWS DATA
# --------------------------------

print("\nLoading classified news dataset...")

if not input_file.exists():
    raise FileNotFoundError(f"Dataset not found: {input_file}")

df = pd.read_csv(input_file)
df = df.fillna("")

required_columns = [
    "source",
    "title",
    "published",
    "link",
    "countries",
    "topics"
]

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required CSV columns: {missing_columns}"
    )

print(f"Articles loaded: {len(df)}")


# --------------------------------
# 3. CONNECT TO SQLITE DATABASE
# --------------------------------

connection = sqlite3.connect(database_file)
cursor = connection.cursor()

print("\nConnected to SQLite database.")


try:

    # --------------------------------
    # 4. CREATE ARTICLES TABLE
    # --------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            source TEXT NOT NULL,

            title TEXT NOT NULL,

            published TEXT,

            link TEXT UNIQUE NOT NULL,

            countries TEXT,

            topics TEXT

        )
    """)

    print("Articles table is ready.")


    # --------------------------------
    # 5. INSERT OR UPDATE ARTICLES
    # --------------------------------

    articles = df[required_columns].itertuples(
        index=False,
        name=None
    )

    cursor.executemany("""

        INSERT INTO articles
        (source, title, published, link, countries, topics)

        VALUES (?, ?, ?, ?, ?, ?)

        ON CONFLICT(link) DO UPDATE SET

            source = excluded.source,
            title = excluded.title,
            published = excluded.published,
            countries = excluded.countries,
            topics = excluded.topics

    """, articles)

    connection.commit()

    print("Articles inserted or updated successfully.")


    # --------------------------------
    # 6. VERIFY DATABASE RECORDS
    # --------------------------------

    cursor.execute("SELECT COUNT(*) FROM articles")
    total_articles = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM articles
        WHERE countries != ''
    """)
    articles_with_countries = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM articles
        WHERE topics != ''
    """)
    articles_with_topics = cursor.fetchone()[0]


    # --------------------------------
    # 7. DISPLAY DATABASE REPORT
    # --------------------------------

    print("\n========== STATECRAFT MONITOR ==========")
    print("             DATABASE REPORT")
    print("========================================")

    print(f"Articles in current CSV: {len(df)}")
    print(f"Total articles in database: {total_articles}")
    print(f"Articles with countries: {articles_with_countries}")
    print(f"Articles with topics: {articles_with_topics}")

    print(f"\nDatabase location:\n{database_file}")


    # Display three sample records

    cursor.execute("""
        SELECT id, source, title, countries, topics
        FROM articles
        ORDER BY id DESC
        LIMIT 3
    """)

    print("\nLATEST DATABASE RECORDS:")

    for article in cursor.fetchall():

        print("\nID:", article[0])
        print("Source:", article[1])
        print("Headline:", article[2])
        print("Countries:", article[3])
        print("Topics:", article[4])
        print("-" * 60)


finally:

    connection.close()
    print("\nDatabase connection closed.")

print("\n========================================")
