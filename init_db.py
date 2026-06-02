import sqlite3

# Connect to a new SQLite database (or opens if exists)
conn = sqlite3.connect("history.db")
cursor = conn.cursor()

# Create a table to store history
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_filename TEXT,
    prompt TEXT,
    gemini_response TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ Database and table created successfully!")
