import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        farmer_username TEXT,
        product_name TEXT,
        price REAL,
        description TEXT
    )
''')

conn.commit()
conn.close()
