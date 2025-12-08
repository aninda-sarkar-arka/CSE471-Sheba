import sqlite3
import sys

db = 'instance/app.db'
conn = sqlite3.connect(db)
cur = conn.cursor()

print('Database file:', db)

print('\n--- user table schema (PRAGMA table_info) ---')
cur.execute("PRAGMA table_info('user')")
cols = cur.fetchall()
for c in cols:
    print(c)

print('\n--- user table columns (via sqlite_master) ---')
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='user'")
row = cur.fetchone()
print(row[0] if row else 'no user table')

username = sys.argv[1] if len(sys.argv) > 1 else 'arka'
print(f"\n--- row for username='{username}' ---")
cur.execute("SELECT * FROM user WHERE username=?", (username,))
row = cur.fetchone()
if not row:
    print('No row found for', username)
else:
    # print columns names from pragma
    names = [c[1] for c in cols]
    for name, val in zip(names, row):
        print(f"{name}: {val}")

conn.close()