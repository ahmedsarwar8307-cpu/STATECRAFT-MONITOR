
import sqlite3

database_path = "database/geointel.db"

connection = sqlite3.connect(database_path)
cursor = connection.cursor()

print("DATABASE TABLES:")
tables = cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
).fetchall()

print(tables)

for table in tables:
    table_name = table[0]

    print("\nTABLE:", table_name)

    columns = cursor.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    for column in columns:
        print(column)

connection.close()
