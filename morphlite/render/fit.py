"""Text-fit helpers: shrink font to fit box."""
from __future__ import annotations
import math

CAVG = {"Arial": 0.55, "Times New Roman": 0.60, "Calibri": 0.50}
MIN_PT = 8.0

def shrink_to_fit(font_name: str, orig_pt: float, text: str, box_w_in: float, box_h_in: float) -> float:
    box_w_cm = box_w_in * 2.54
    box_h_cm = box_h_in * 2.54
    avg = CAVG.get(font_name, 0.55)
    for pt in range(int(orig_pt), int(MIN_PT)-1, -1):
        # rough: chars per line ~ box_w / (pt*0.035*avg*1.25)
        cpl = max(8, int(box_w_cm / (pt * 0.0352778 * avg * 1.05)))
        lines = math.ceil(len(text) / cpl) if text else 1
        h_cm = lines * pt * 0.0352778 * 1.25
        if h_cm <= box_h_cm:
            return float(pt)
    return MIN_PT
