import sqlite3

conn = sqlite3.connect('instance/app.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall()]
print("Tables:", tables)

# Show users
print("\n--- USERS ---")
cursor.execute("SELECT id, username, name, role, location, service_area FROM user;")
for row in cursor.fetchall():
    print(row)

# Show services
print("\n--- SERVICES ---")
cursor.execute("SELECT id, provider_id, title, category, price FROM service;")
for row in cursor.fetchall():
    print(row)

conn.close()
print("\nDone.")
