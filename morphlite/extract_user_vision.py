from pathlib import Path
import re

path = Path(r"C:\Users\Akshay.JOHN-XAVIER\OneDrive - Akkodis\Documents\Me\session-ses_brandmorph.md")
text = path.read_text(encoding="utf-8", errors="ignore")

# Match ## User sections
pattern = re.compile(r'## User[^\n]*\n+(.*?)(?=\n## (?:Assistant|User)|\Z)', re.DOTALL)
matches = pattern.findall(text)

print(f"Total user messages found: {len(matches)}")

summary_file = Path(r"C:\Users\Akshay.JOHN-XAVIER\.gemini\antigravity-ide\scratch\BrandMorph\user_requirements_summary.md")
summary_lines = [
    "# Complete User Directives & Vision (From session-ses_brandmorph.md)\n",
    f"**Total User Messages Extracted:** {len(matches)}\n",
    "---"
]

for idx, content in enumerate(matches):
    clean = content.strip()
    if clean:
        summary_lines.append(f"### Message {idx + 1}\n\n{clean}\n\n---")

summary_file.write_text("\n".join(summary_lines), encoding="utf-8")
print(f"Summary written to {summary_file}")
