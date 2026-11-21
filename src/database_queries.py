
import sqlite3

from pathlib import Path


# --------------------------------
# 1. CONNECT TO DATABASE
# --------------------------------

project_folder = Path(__file__).resolve().parent.parent

database_file = project_folder / "database" / "geointel.db"

connection = sqlite3.connect(database_file)

cursor = connection.cursor()


# --------------------------------
# 2. QUERY 1: SHOW ALL ARTICLES
# --------------------------------

print("\n========== ALL ARTICLES ==========")

cursor.execute("""
    SELECT id, title
    FROM articles
""")

for article in cursor.fetchall():

    print(article[0], "-", article[1])


# --------------------------------
# 3. QUERY 2: SEARCH BY COUNTRY
# --------------------------------

country = "Ukraine"

print(f"\n========== {country.upper()} NEWS ==========")

cursor.execute("""
    SELECT title, countries
    FROM articles
    WHERE countries LIKE ?
""", (f"%{country}%",))

for article in cursor.fetchall():

    print("\nHeadline:", article[0])
    print("Countries:", article[1])


# --------------------------------
# 4. QUERY 3: SEARCH BY TOPIC
# --------------------------------

topic = "Diplomacy"

print(f"\n========== {topic.upper()} NEWS ==========")

cursor.execute("""
    SELECT title, topics
    FROM articles
    WHERE topics LIKE ?
""", (f"%{topic}%",))

for article in cursor.fetchall():

    print("\nHeadline:", article[0])
    print("Topics:", article[1])


# --------------------------------
# 5. QUERY 4: SEARCH BY NEWS SOURCE
# --------------------------------

print("\n========== BBC ARTICLES ==========")

cursor.execute("""
    SELECT title, source
    FROM articles
    WHERE source = 'BBC'
""")

for article in cursor.fetchall():

    print("\nHeadline:", article[0])
    print("Source:", article[1])

# --------------------------------
# 6. QUERY: SORT ARTICLES
# --------------------------------

print("\n========== ARTICLES BY INSERTION ORDER ==========")

cursor.execute("""
    SELECT id, title
    FROM articles
    ORDER BY id DESC
    LIMIT 5
""")

for article in cursor.fetchall():

    print(article[0], "-", article[1])


# --------------------------------
# 6. QUERY 5: COUNT ARTICLES
# --------------------------------

print("\n========== COUNTRY ARTICLE COUNT ==========")

cursor.execute("""
    SELECT COUNT(*)
    FROM articles
    WHERE countries LIKE '%China%'
""")

china_count = cursor.fetchone()[0]

print("Articles mentioning China:", china_count)


# --------------------------------
# 7. QUERY: COUNT ARTICLES BY SOURCE
# --------------------------------

print("\n========== ARTICLES BY NEWS SOURCE ==========")

cursor.execute("""
    SELECT source, COUNT(*) AS article_count
    FROM articles
    GROUP BY source
    ORDER BY article_count DESC
""")

for row in cursor.fetchall():

    print(row[0], "-", row[1], "articles")


# --------------------------------
# 7. CLOSE CONNECTION
# --------------------------------

connection.close()

print("\nDatabase connection closed.")
