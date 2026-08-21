import sqlite3
import json
from pathlib import Path
from datetime import datetime

db_path = Path(r"C:\Users\Akshay.JOHN-XAVIER\.local\share\opencode\opencode.db")
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

session_id = "ses_fdb255015ffer0l40SVqxAKhZf"

# Get session info
session_row = cur.execute("SELECT * FROM session WHERE id=?", (session_id,)).fetchone()
print("Session:", session_row)

# Get all parts/messages for this session
parts = cur.execute("SELECT * FROM part WHERE session_id=? ORDER BY rowid ASC", (session_id,)).fetchall()
print(f"Total parts found: {len(parts)}")

part_cols = [c[1] for c in cur.execute("PRAGMA table_info(part)").fetchall()]

md_lines = [
    f"# OpenCode Session Export: `{session_id}`",
    f"**Exported At**: {datetime.now().isoformat()}",
    f"**Title**: Current model identification",
    f"**Working Directory**: `C:/Users/Akshay.JOHN-XAVIER/OneDrive - Akkodis/Documents/Me/opencode`",
    "",
    "---",
    ""
]

for p in parts:
    p_dict = dict(zip(part_cols, p))
    # Extract text or content
    content = p_dict.get("text") or p_dict.get("data") or p_dict.get("content") or ""
    if not content:
        # Check all values in dict
        for k, v in p_dict.items():
            if isinstance(v, str) and len(v) > 20 and k not in ("id", "session_id", "message_id"):
                content = v
                break
    
    sender = p_dict.get("role") or p_dict.get("type") or "Message"
    md_lines.append(f"### {sender.upper()}\n")
    md_lines.append(f"{content}\n\n---\n")

full_md = "\n".join(md_lines)

# Save to opencode dir and BrandMorph
out1 = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\opencode\session-ses_fdb2.md")
out1.parent.mkdir(parents=True, exist_ok=True)
out1.write_text(full_md, encoding="utf-8")

out2 = Path(r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\scratch\BrandMorph\session-ses_fdb2.md")
out2.write_text(full_md, encoding="utf-8")

print(f"Saved successfully to:\n1. {out1}\n2. {out2}")
