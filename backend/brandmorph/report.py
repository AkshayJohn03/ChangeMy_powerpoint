"""MorphReport: the trust artifact.

Enterprise users will not accept a silently mutated deck. Every transformation
decision is logged (what, where, why, how confident) so a reviewer can audit or
revert. The report also proves idempotence (second run logs zero changes).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


@dataclass
class ChangeEntry:
    stage: str  # theme | format | font | copy | fit
    slide: int | None
    element: str
    kind: str  # color | font | text | size
    before: str
    after: str
    role: str = ""
    delta_e: float = 0.0
    confidence: float = 1.0
    note: str = ""

    def as_dict(self) -> dict:
        return {
            "stage": self.stage, "slide": self.slide, "element": self.element,
            "kind": self.kind, "before": self.before, "after": self.after,
            "role": self.role, "delta_e": round(self.delta_e, 2),
            "confidence": round(self.confidence, 2), "note": self.note,
        }


@dataclass
class MorphReport:
    source: str = ""
    brand: str = ""
    dry_run: bool = False
    entries: list[ChangeEntry] = field(default_factory=list)
    review_flags: list[str] = field(default_factory=list)
    inventory: dict = field(default_factory=dict)
    idempotence_hash: str = ""

    def add(self, entry: ChangeEntry) -> None:
        self.entries.append(entry)

    @property
    def total_changes(self) -> int:
        return len(self.entries)

    def flag(self, message: str) -> None:
        self.review_flags.append(message)

    @property
    def counts_by_stage(self) -> dict:
        out: dict[str, int] = {}
        for e in self.entries:
            out[e.stage] = out.get(e.stage, 0) + 1
        return out

    def finalize(self) -> MorphReport:
        payload = json.dumps([e.as_dict() for e in self.entries], sort_keys=True)
        self.idempotence_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]
        return self

    def to_json(self) -> dict:
        return {
            "source": self.source,
            "brand": self.brand,
            "dry_run": self.dry_run,
            "total_changes": len(self.entries),
            "counts_by_stage": self.counts_by_stage,
            "review_flags": self.review_flags,
            "inventory": self.inventory,
            "idempotence_hash": self.idempotence_hash,
            "changes": [e.as_dict() for e in self.entries],
        }

    def to_markdown(self) -> str:
        lines = [
            "# BrandMorph morph report",
            "",
            f"- **Source deck:** `{self.source}`",
            f"- **Brand:** {self.brand}",
            f"- **Dry run:** {self.dry_run}",
            f"- **Total changes:** {len(self.entries)}",
            f"- **Idempotence hash:** `{self.idempotence_hash}`",
            "",
            "## Changes by stage",
            "",
        ]
        for stage, count in sorted(self.counts_by_stage.items()):
            lines.append(f"- `{stage}`: {count}")
        if self.review_flags:
            lines += ["", "## Needs manual review", ""]
            lines += [f"- {f}" for f in self.review_flags]
        lines += ["", "## Change log", "",
                  "| stage | slide | element | kind | before | after | role | dE | note |",
                  "|---|---|---|---|---|---|---|---|---|"]
        for e in self.entries:
            lines.append(
                f"| {e.stage} | {e.slide if e.slide is not None else '-'} | {e.element} "
                f"| {e.kind} | {e.before} | {e.after} | {e.role} "
                f"| {e.delta_e:.1f} | {e.note} |"
            )
        return "\n".join(lines) + "\n"
