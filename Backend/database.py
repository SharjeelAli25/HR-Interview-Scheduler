import sqlite3
import json
from datetime import datetime
 
# Simple SQLite database setup
# We use a single .db file stored locally
 
DB_PATH = "interviews.db"
 
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    # Create interviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            scheduled_date TEXT
        )
    """)

    # If an older DB exists without scheduled_date, add the column
    cursor.execute("PRAGMA table_info(interviews)")
    cols = [r[1] for r in cursor.fetchall()]
    if 'scheduled_date' not in cols:
        try:
            cursor.execute("ALTER TABLE interviews ADD COLUMN scheduled_date TEXT")
        except Exception:
            pass

    conn.commit()
    conn.close()
    print(f"✓ Database initialized at {DB_PATH} (scheduled_date supported)")
 
def get_all_interviews():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return results as dictionaries
    cursor = conn.cursor()
   
    cursor.execute("SELECT * FROM interviews ORDER BY created_at DESC")
    interviews = [dict(row) for row in cursor.fetchall()]
   
    conn.close()
    return interviews
 
def create_interview(title, description="", scheduled_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    cursor.execute(
        "INSERT INTO interviews (title, description, scheduled_date) VALUES (?, ?, ?)",
        (title, description, scheduled_date)
    )
   
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
   
    # Return the created interview
    return {
        "id": new_id,
        "title": title,
        "description": description,
        "scheduled_date": scheduled_date,
        "created_at": datetime.now().isoformat()
    }
 
def update_interview(interview_id, title=None, description=None, scheduled_date=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    updates = []
    params = []
    if title is not None:
        updates.append("title = ?")
        params.append(title)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if scheduled_date is not None:
        updates.append("scheduled_date = ?")
        params.append(scheduled_date)
    if not updates:
        conn.close()
        return False

    params.append(interview_id)
    cursor.execute(f"UPDATE interviews SET {', '.join(updates)} WHERE id = ?", tuple(params))
   
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed
 
def delete_interview(interview_id):
    """
    Delete an interview by ID.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
   
    cursor.execute("DELETE FROM interviews WHERE id = ?", (interview_id,))
   
    conn.commit()
    conn.close()


def get_interview_by_id(interview_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None