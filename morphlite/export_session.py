import sqlite3
import json
from pathlib import Path

db_path = Path(r"C:\Users\Akshay.JOHN-XAVIER\.local\share\opencode\opencode.db")
if not db_path.exists():
    print("Database not found")
    exit()

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Get all tables
tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

# Search sessions
if "session" in tables:
    sessions = cur.execute("SELECT * FROM session").fetchall()
    print(f"Total sessions: {len(sessions)}")
    for s in sessions:
        print("Session row:", s)

if "message" in tables:
    msgs = cur.execute("SELECT session_id, count(*) FROM message GROUP BY session_id").fetchall()
    print("Messages per session:", msgs)

# Search for fdb2 across all tables
for t in tables:
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
    for col in cols:
        try:
            res = cur.execute(f"SELECT * FROM {t} WHERE cast({col} as text) LIKE '%fdb2%'").fetchall()
            if res:
                print(f"Match in {t}.{col}:", res)
        except Exception:
            pass
