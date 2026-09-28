"""BrandMorph v2 — in-place PowerPoint re-branding engine.

v1 decompiled decks and rebuilt them from blank layouts (destroying charts,
tables, layouts and fidelity). v2 transforms the deck in place: theme surgery
at the OOXML level, role-aware mapping of explicit formatting, font role
assignment, length-budgeted copy rewriting and a full change report.
See docs/V2_DESIGN.md for the approved design.
"""

__version__ = "2.0.0"
