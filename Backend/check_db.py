import database
import sqlite3
import os

print('DB path:', database.DB_PATH)
print('Exists?', os.path.exists(database.DB_PATH))
conn = sqlite3.connect(database.DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interviews';")
print('Table exists before init:', bool(cur.fetchone()))
conn.close()

print('Running init_db()...')
database.init_db()

conn = sqlite3.connect(database.DB_PATH)
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interviews';")
print('Table exists after init:', bool(cur.fetchone()))
conn.close()

print('Interviews:', database.get_all_interviews())
