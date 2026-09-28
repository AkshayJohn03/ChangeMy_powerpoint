"""CLI end-to-end: python -m brandmorph apply on a fixture deck."""

import subprocess
import sys

BACKEND = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_cli_apply_end_to_end(tmp_path, akkodis):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    out = tmp_path / "out.pptx"
    report_dir = tmp_path / "report"

    proc = subprocess.run(
        [
            sys.executable, "-m", "brandmorph", "apply",
            "--deck", str(src), "--brand", "akkodis",
            "--out", str(out), "--report", str(report_dir),
        ],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert out.exists() and out.stat().st_size > 10_000
    md = (report_dir / "morph_report.md").read_text(encoding="utf-8")
    assert "morph report" in md.lower()
    assert "Total changes" in md
    assert (report_dir / "morph_report.json").exists()


def test_cli_dry_run(tmp_path):
    from conftest import build_themed

    src = build_themed(tmp_path / "deck.pptx")
    missing = tmp_path / "nope.pptx"
    proc = subprocess.run(
        [
            sys.executable, "-m", "brandmorph", "apply",
            "--deck", str(src), "--brand", "corporate_light",
            "--out", str(missing), "--dry-run",
        ],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=180,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert not missing.exists()


def test_cli_inventory(tmp_path):
    from conftest import build_hardcoded

    src = build_hardcoded(tmp_path / "deck.pptx")
    proc = subprocess.run(
        [sys.executable, "-m", "brandmorph", "inventory", "--deck", str(src)],
        cwd=str(BACKEND), capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert '"slide_count": 1' in proc.stdout
