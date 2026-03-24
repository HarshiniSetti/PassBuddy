import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE requests ADD COLUMN scanned INTEGER DEFAULT 0")
except:
    print("scanned column already exists")

try:
    cursor.execute("ALTER TABLE requests ADD COLUMN out_time TEXT")
except:
    print("out_time column already exists")

try:
    cursor.execute("ALTER TABLE requests ADD COLUMN in_time TEXT")
except:
    print("in_time column already exists")

conn.commit()
conn.close()

print("Database updated successfully!")