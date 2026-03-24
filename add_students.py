import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# 🔥 Clear old data first
cursor.execute("DELETE FROM students")

students = [
    ("N220510", "Harshini", "18F22"),
    ("N220019", "Sudhi", "94QWW"),
    ("N220032", "Sanju", "28SNN"),
    ("N220504", "Kiran", "pass4"),
    ("N220505", "Sneha", "pass5"),
    ("N220506", "Arjun", "pass6"),
    ("N220507", "Divya", "pass7"),
    ("N220508", "Vikram", "pass8"),
    ("N220509", "Pooja", "pass9"),
    ("N220501", "Ravi", "pass10")
]

cursor.executemany("""
INSERT INTO students (student_id, name, password)
VALUES (?, ?, ?)
""", students)

conn.commit()
conn.close()

print("✅ Students reset & added!")