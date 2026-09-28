"""MorphPipeline: orchestration of the v2 stages.

Order matters (design §2):
  analyze -> format mapping -> font roles -> copy rewrite -> fit guard
        -> save -> theme surgery (zip level) -> report

Dry run performs every stage against a throwaway copy so the report is a
complete *plan* without producing an output deck.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from pptx import Presentation

from ..brand.profile import BrandDNA
from ..report import MorphReport
from .analyzer import analyze
from .copy import CopyToneRewriter, LLMClient
from .fit import FitGuard
from .fonts import FontRoleMapper
from .format_mapper import DirectFormatMapper
from .theme import transform as transform_theme


@dataclass
class MorphOptions:
    dry_run: bool = False
    rewrite_copy: bool | None = None  # None -> defer to BrandDNA.rules
    fit_guard: bool = True


class MorphPipeline:
    def __init__(
        self,
        dna: BrandDNA,
        llm: LLMClient | None = None,
        options: MorphOptions | None = None,
    ):
        self.dna = dna
        self.llm = llm
        self.options = options or MorphOptions()

    def run(self, source, output, report_dir: str | None = None) -> MorphReport:
        opts = self.options
        report = MorphReport(source=str(source), brand=self.dna.name, dry_run=opts.dry_run)
        report.inventory = analyze(source)

        prs = Presentation(str(source))
        DirectFormatMapper(self.dna, report).run(prs)
        FontRoleMapper(self.dna, report).run(prs)

        rewrite = (
            opts.rewrite_copy if opts.rewrite_copy is not None else self.dna.rules.rewrite_copy
        )
        CopyToneRewriter(self.dna, self.llm if rewrite else None).apply(prs, report)

        if opts.fit_guard:
            FitGuard(self.dna, report).run(prs)

        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)

        if opts.dry_run:
            # theme plan: diff is computed against a throwaway save (no output)
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td) / "dry_run.pptx"
                prs.save(str(tmp))
                transform_theme(tmp, self.dna, report)
        else:
            prs.save(str(out))
            transform_theme(out, self.dna, report)

        report.finalize()
        if report_dir:
            d = Path(report_dir)
            d.mkdir(parents=True, exist_ok=True)
            (d / "morph_report.md").write_text(report.to_markdown(), encoding="utf-8")
            (d / "morph_report.json").write_text(
                json.dumps(report.to_json(), indent=2), encoding="utf-8"
            )
        return report
