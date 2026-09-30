import sqlite3

conn = sqlite3.connect("backend/clauseguard_fallback.db")
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables:", tables)

try:
    docs = c.execute("SELECT id, name, status, error_message, clause_count, page_count FROM documents").fetchall()
    print("Documents in DB:")
    for d in docs:
        print(d)
except Exception as e:
    print("Error querying documents:", e)
