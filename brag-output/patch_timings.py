"""Patch composition/index.html timing tokens from voiceover-durations.json."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
durs = json.loads((ROOT / "voiceover-durations.json").read_text())
vo = [durs[f"scene{i:02d}"] for i in range(1, 12)]

# scene duration = narration + 0.35s lead-in + ~0.55s tail
D = [round(v + 0.9, 3) for v in vo]
S = [0.0]
for d in D[:-1]:
    S.append(round(S[-1] + d, 3))
END = round(S[-1] + D[-1], 3)
LASTLOOP = round(END - 352.152, 3)

html = (ROOT / "composition" / "index.html").read_text(encoding="utf-8")

def scene_start(n: int) -> str:
    return f"{S[n-1]:.3f}"

# simple tokens
for i in range(1, 12):
    html = html.replace(f"@@D{i}@@", f"{D[i-1]:.3f}")
    html = html.replace(f"@@VO{i}@@", f"{vo[i-1]:.3f}")
    html = html.replace(f"@@S{i}@@", scene_start(i))

# expressions: @@S<n>+<off>@@ and @@END[-<off>]@@
def expr(m: re.Match) -> str:
    body = m.group(1)
    if body == "LASTLOOP":
        return f"{LASTLOOP:.3f}"
    if body.startswith("END"):
        val = END
        off = body[3:]
    else:
        base = re.split(r"[+\-]", body)[0]       # e.g. "S2"
        off = body[len(base):]                   # e.g. "+0.35" or ""
        val = S[int(base[1:]) - 1]
    if off:
        val += float(off)
    return f"{val:.3f}"

html = re.sub(r"@@([A-Z0-9]+(?:[+\-][0-9.]+)?)@@", expr, html)
html = html.replace("@@LASTLOOP@@", f"{LASTLOOP:.3f}")
html = html.replace("@@END@@", f"{END:.3f}")

(ROOT / "composition" / "index.html").write_text(html, encoding="utf-8")

print("scene starts:", [f"{s:.3f}" for s in S])
print("durations:", [f"{d:.3f}" for d in D])
print(f"END={END:.3f}  LASTLOOP={LASTLOOP:.3f}")
left = re.findall(r"@@[A-Z0-9.+\-]+@@", html)
print("unresolved tokens:", left or "none")
