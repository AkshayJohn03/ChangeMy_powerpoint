"""Pair discovery and validation over extracted ASTs.

Identity resolution hierarchy (canonical deck join):
    1. MD5 content hash      confidence 1.00
    2. name_key + bucket     confidence 0.90
    3. normalized filename   confidence 0.70
    4. unresolved            -> skipped/review

Stages:
  1. validate auto-detected deck pairs via slide-level text matching
  2. resolve review-bucket variant decks
  3. Category B alternation scan: offsets {1,2,3}, best-vs-second margin,
     variant deduped, full diagnostics
"""
from __future__ import annotations

import json
import math
import statistics
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from .. import config
from ..ast import extractor
from ..ast.node_ids import slugify
from . import textsim

AST_ROOT = config.EXTRACTED_DIR / "ast"
PAIRS_DIR = config.PAIRS_DIR

BRAND_COLORS = {"FFB81C", "00FFFF", "030C1E", "081632"}
BRAND_FONTS = {"times new roman", "arial", "roboto"}

VALIDATE_THRESHOLD = 0.60
REJECT_THRESHOLD = 0.35
ALT_OFFSETS = (1, 2, 3)
ALT_MARGIN = 0.08
ALT_MIN_SIM = 0.45
ALT_MIN_CONT = 0.40


class ManifestIndexes:
    def __init__(self, manifest: list[dict], file_manifest: list[dict]):
        self.records = manifest
        self.by_source = {r["source"]: r for r in manifest}
        self.fm_by_orig = {r["path"]: r for r in file_manifest if r.get("path")}
        self.by_md5: dict[str, dict] = {}
        self.by_name_bucket: dict[tuple, list[dict]] = defaultdict(list)
        self.by_norm_name: dict[str, dict] = {}

        for fm in file_manifest:
            dest = fm.get("dest")
            if not dest:
                continue
            rec = self.by_source.get(dest)
            if not rec:
                continue
            md5 = fm.get("md5")
            if md5:
                self.by_md5[md5] = rec
            self.by_name_bucket[(rec["name_key"], rec["bucket"])].append(rec)
            self.by_norm_name.setdefault(slugify(Path(rec["source"]).stem), rec)

    def resolve(self, orig_path: str | None, name_key: str, want_bucket: str) -> tuple[dict | None, str, float]:
        fm = self.fm_by_orig.get(orig_path or "")
        if fm:
            hit = self.by_md5.get(fm.get("md5", ""))
            if hit is not None and (hit["bucket"] == want_bucket or hit["bucket"] in ("paired_raw", "paired_branded", "branded_only", "alternating", "raw_only", "review")):
                return hit, "md5", 1.0
        hits = self.by_name_bucket.get((name_key, want_bucket)) or []
        if hits:
            return hits[0], "name_key_bucket", 0.90
        if orig_path:
            hit = self.by_norm_name.get(slugify(Path(orig_path).stem))
            if hit is not None:
                return hit, "normalized_name", 0.70
        return None, "unresolved", 0.0


def load_ast_manifest() -> list[dict]:
    with open(AST_ROOT / "extraction_manifest.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def load_file_manifest() -> list[dict]:
    with open(config.METADATA_DIR / "file_manifest.jsonl", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh]


def load_deck(rec: dict) -> dict:
    return json.loads(Path(rec["ast_path"]).read_text(encoding="utf-8"))


_text_cache: dict[str, list[str]] = {}


def slide_texts(deck: dict) -> list[str]:
    key = deck.get("deck_id") or f"id_{id(deck)}"
    if key not in _text_cache:
        _text_cache[key] = [extractor.slide_text(deck, i) for i in range(len(deck["slides"]))]
    return _text_cache[key]


def match_slides(texts_a: list[str], texts_b: list[str]) -> list[dict]:
    entries = []
    for i, ta in enumerate(texts_a):
        for j, tb in enumerate(texts_b):
            s = textsim.similarity(ta, tb)
            if s > 0.05:
                entries.append((s, i, j))
    entries.sort(key=lambda e: (-e[0], e[1], e[2]))

    used_a: set[int] = set()
    used_b: set[int] = set()
    mappings = []
    for s, i, j in entries:
        if i in used_a or j in used_b:
            continue
        used_a.add(i)
        used_b.add(j)
        mappings.append({"raw_index": i, "branded_index": j, "similarity": s})
    mappings.sort(key=lambda m: m["raw_index"])
    return mappings


def brand_score(deck: dict, slide_index: int) -> float:
    score = 0.0
    slide = deck["slides"][slide_index]

    def walk(nodes):
        nonlocal score
        for n in nodes:
            if n.get("fill_color") in BRAND_COLORS:
                score += 1.0
            for p in n.get("paragraphs") or []:
                for r in p.get("runs"):
                    fam = (r.get("font_family") or "").lower()
                    if fam in BRAND_FONTS:
                        score += 0.5
                    if r.get("color") in BRAND_COLORS:
                        score += 1.5
            walk(n.get("children") or [])

    walk(slide["nodes"])
    bg = (slide.get("background_color") or "").upper()
    if bg in BRAND_COLORS:
        score += 3.0
    return score


def structure_similarity(deck_a: dict, deck_b: dict, mappings: list[dict]) -> float:
    vals = []

    def type_hist(nodes):
        return Counter(n["type"] for n in extractor.flatten_nodes(nodes))

    for m in mappings:
        ha = type_hist(deck_a["slides"][m["raw_index"]]["nodes"])
        hb = type_hist(deck_b["slides"][m["branded_index"]]["nodes"])
        union = sum((ha + hb).values()) - sum((ha & hb).values())
        vals.append(sum((ha & hb).values()) / union if union else 0.0)
    return round(statistics.mean(vals), 4) if vals else 0.0


def validate_auto_pairs(manifest: list[dict]) -> tuple[list[dict], list[dict]]:
    PAIRS_DIR.mkdir(parents=True, exist_ok=True)
    idx = ManifestIndexes(manifest, load_file_manifest())

    with open(config.METADATA_DIR / "pairs_auto_detected.jsonl", encoding="utf-8") as fh:
        pairs = [json.loads(line) for line in fh]

    validated, rejected, skipped = [], [], []
    seq = 0
    for p in pairs:
        raw_rec, join_r, conf_r = idx.resolve(p.get("raw_slide"), p["key"], "paired_raw")
        bran_rec, join_b, conf_b = idx.resolve(p.get("branded_slide"), p["key"], "paired_branded")
        if not raw_rec or not bran_rec:
            skipped.append({"pair_id": p["pair_id"], "key": p["key"], "reason": "unresolved_identity"})
            continue

        raw_deck, bran_deck = load_deck(raw_rec), load_deck(bran_rec)
        t_raw, t_bran = slide_texts(raw_deck), slide_texts(bran_deck)
        mappings = match_slides(t_raw, t_bran)

        sims = [m["similarity"] for m in mappings] or [0.0]
        mean_sim = round(sum(sims) / len(sims), 4)
        covered = len(mappings) / max(len(t_raw), len(t_bran), 1)
        struct_sim = structure_similarity(raw_deck, bran_deck, mappings)

        seq += 1
        status = (
            "VALIDATED" if mean_sim >= VALIDATE_THRESHOLD and covered >= 0.6
            else "REJECTED" if mean_sim < REJECT_THRESHOLD
            else "PARTIAL"
        )
        verdict = {
            "pair_id": p["pair_id"],
            "deck_pair_id": f"dpair_{seq:04d}",
            "basis": p["basis"],
            "name_key": p["key"],
            "join_method": join_r if join_r == join_b else f"{join_r}|{join_b}",
            "join_confidence": round(min(conf_r, conf_b), 2),
            "raw_deck": raw_rec["deck_id"],
            "branded_deck": bran_rec["deck_id"],
            "slide_count_raw": len(t_raw),
            "slide_count_branded": len(t_bran),
            "slide_alignment": {
                "matched": len(mappings),
                "unmatched_raw": len(t_raw) - len(mappings),
                "unmatched_branded": len(t_bran) - len(mappings),
            },
            "content_similarity": mean_sim,
            "min_slide_similarity": min(sims),
            "structure_similarity": struct_sim,
            "coverage": round(covered, 4),
            "status": status,
            "validation": "accepted" if status == "VALIDATED" else "accepted_with_review" if status == "PARTIAL" else "rejected",
            "slide_mappings": [
                {
                    "pair_id": f"{p['pair_id']}_s{m['raw_index'] + 1:03d}",
                    "raw_slide_id": raw_deck["slides"][m["raw_index"]]["slide_id"],
                    "branded_slide_id": bran_deck["slides"][m["branded_index"]]["slide_id"],
                    "similarity": m["similarity"],
                }
                for m in mappings
            ],
        }
        (validated if status in ("VALIDATED", "PARTIAL") else rejected).append(verdict)
        print(f"  {verdict['deck_pair_id']} {status:9s} join={verdict['join_method']:16s} sim={mean_sim:.2f} struct={struct_sim:.2f} cov={covered:.2f} {p['key'][:40]}", flush=True)

    if skipped:
        with open(PAIRS_DIR / "skipped_pairs.jsonl", "w", encoding="utf-8") as fh:
            for s in skipped:
                fh.write(json.dumps(s) + "\n")
        print(f"  SKIPPED: {len(skipped)}", flush=True)
    return validated, rejected


def resolve_review_decks(manifest: list[dict]) -> list[dict]:
    review = [r for r in manifest if r["bucket"] == "review"]
    others = [r for r in manifest if r["bucket"] not in ("review", "template")]

    by_key: dict[str, list[dict]] = defaultdict(list)
    for r in others:
        by_key[r["name_key"]].append(r)

    resolved = []
    for rec in review:
        deck_r = load_deck(rec)
        texts_r = slide_texts(deck_r)

        candidates = list(by_key.get(rec["name_key"], []))
        seen = {rec["name_key"]}
        if not candidates:
            for k in by_key:
                if k in seen:
                    continue
                if k and SequenceMatcher(None, k, rec["name_key"]).ratio() >= 0.85:
                    candidates.extend(by_key[k])
                    seen.add(k)

        best = None
        for cand in candidates:
            deck_c = load_deck(cand)
            texts_c = slide_texts(deck_c)
            mappings = match_slides(texts_r, texts_c)
            sims = [m["similarity"] for m in mappings] or [0.0]
            mean_sim = sum(sims) / len(sims)
            if best is None or mean_sim > best["_mean"]:
                best = {"candidate": cand, "_mean": mean_sim, "mean_similarity": round(mean_sim, 4), "cand_bucket": cand["bucket"]}

        entry = {
            "review_deck": rec["deck_id"],
            "name_key": rec["name_key"],
            "best_match_deck": best["candidate"]["deck_id"] if best else None,
            "best_match_bucket": best["cand_bucket"] if best else None,
            "mean_similarity": best["mean_similarity"] if best else 0.0,
            "resolution": "UNRESOLVED",
        }
        if best and best["_mean"] >= 0.75:
            entry["resolution"] = {
                "paired_raw": "RAW_VARIANT_OF_PAIRED_RAW",
                "paired_branded": "CLEAN_VARIANT_OF_PAIRED_BRANDED",
            }.get(best["cand_bucket"], "RAW_VARIANT_CANDIDATE" if best["cand_bucket"] in ("raw_only", "alternating") else "CLEAN_VARIANT_CANDIDATE")
        elif best and best["_mean"] >= 0.45:
            entry["resolution"] = "WEAK_MATCH_NEEDS_MANUAL"
        resolved.append(entry)
        print(f"  {entry['resolution']:34s} sim={entry['mean_similarity']:.2f} {rec['name_key'][:44]}", flush=True)
    return resolved


def detect_alternation(manifest: list[dict]) -> tuple[list[dict], dict]:
    alts = [r for r in manifest if r["bucket"] == "alternating"]

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in alts:
        groups[r["name_key"]].append(r)

    representatives, variants_map = [], {}
    for key, members in sorted(groups.items()):
        rep = max(members, key=lambda m: (m.get("n_slides") or 0, m["deck_id"]))
        representatives.append(rep)
        variants_map[rep["deck_id"]] = sorted(m["deck_id"] for m in members if m["deck_id"] != rep["deck_id"])

    print(f"  alternating decks: {len(alts)} -> logical decks: {len(representatives)}", flush=True)

    all_scores: list[float] = []
    prepared = []
    for rec in representatives:
        deck = load_deck(rec)
        texts = slide_texts(deck)
        brand = [brand_score(deck, i) for i in range(len(texts))]
        pairs_matrix: dict[int, dict[int, float]] = {}
        for i in range(len(texts)):
            row = {}
            for off in ALT_OFFSETS:
                for j in (i - off, i + off):
                    if 0 <= j < len(texts) and j != i:
                        row[j] = max(row.get(j, 0.0), textsim.similarity(texts[i], texts[j]))
            pairs_matrix[i] = row
            all_scores.extend(v for v in row.values() if v > 0)
        prepared.append((rec, deck, texts, brand, pairs_matrix))

    ordered = sorted(all_scores)
    pct = {q: round(ordered[int(q / 100 * (len(ordered) - 1))], 4) for q in (25, 50, 75, 90) } if ordered else {}

    found = []
    per_deck = []
    for rec, deck, texts, brand, matrix in prepared:
        consumed: set[int] = set()
        deck_found = []
        for i in range(len(texts)):
            if i in consumed:
                continue
            cands = sorted(((s, j) for j, s in matrix[i].items() if j not in consumed and s >= ALT_MIN_SIM), reverse=True)
            if not cands:
                continue
            best_s, best_j = cands[0]
            second_s = cands[1][0] if len(cands) > 1 else 0.0
            cont = textsim.containment(texts[i], texts[best_j])
            if cont < ALT_MIN_CONT:
                continue
            if best_s - second_s < ALT_MARGIN:
                continue
            direction = "unclear"
            if brand[i] > brand[best_j] * 1.2:
                direction = "anchor_clean"
            elif brand[best_j] > brand[i] * 1.2:
                direction = "partner_clean"
            clean_i, raw_i = (i, best_j) if direction == "anchor_clean" else (best_j, i)
            if direction == "unclear":
                clean_i, raw_i = (i, best_j) if brand[i] >= brand[best_j] else (best_j, i)
            deck_found.append(
                {
                    "pair_id": f"alt_{rec['deck_id']}_s{min(i, best_j) + 1:03d}",
                    "deck_id": rec["deck_id"],
                    "cleaner_slide_id": deck["slides"][clean_i]["slide_id"],
                    "rawer_slide_id": deck["slides"][raw_i]["slide_id"],
                    "slide_indices": sorted([i + 1, best_j + 1]),
                    "direction": direction if direction != "unclear" else "assumed_anchor_clean",
                    "brand_score_cleaner": max(brand[i], brand[best_j]),
                    "brand_score_rawer": min(brand[i], brand[best_j]),
                    "similarity": best_s,
                    "runner_up_similarity": second_s,
                    "margin": round(best_s - second_s, 4),
                    "status": "AUTO_CANDIDATE",
                }
            )
            consumed.update((i, best_j))
        found.extend(deck_found)
        adj_profile = [matrix[i].get(i + 1, 0.0) for i in range(len(texts) - 1)]
        per_deck.append(
            {
                "deck_id": rec["deck_id"],
                "name_key": rec["name_key"],
                "variant_decks": variants_map.get(rec["deck_id"], []),
                "n_slides": len(texts),
                "pairs_found": len(deck_found),
                "max_adjacent_sim": round(max(adj_profile), 4) if adj_profile else None,
                "max_any_offset_sim": round(max((max(r.values()) for r in matrix.values() if r), default=0.0), 4),
                "adjacent_similarities": adj_profile,
            }
        )
        print(f"  {rec['name_key'][:48]:50s} slides={len(texts):3d} pairs={len(deck_found)}", flush=True)

    hist = Counter(
        "<0.30" if s < 0.30 else "0.30-0.50" if s < 0.50 else "0.50-0.70" if s < 0.70 else "0.70-0.85" if s < 0.85 else ">=0.85"
        for s in all_scores
    )
    diagnostics = {
        "thresholds": {"min_similarity": ALT_MIN_SIM, "margin": ALT_MARGIN, "offsets": list(ALT_OFFSETS)},
        "candidate_score_percentiles": pct,
        "candidate_score_histogram": dict(sorted(hist.items())),
        "decks_logical": len(representatives),
        "decks_variants_merged": len(alts) - len(representatives),
        "per_deck": per_deck,
    }
    return found, diagnostics


def write_outputs(validated, rejected, review_resolutions, alternation, alt_diagnostics) -> dict:
    PAIRS_DIR.mkdir(parents=True, exist_ok=True)

    def dump(name, rows):
        with open(PAIRS_DIR / name, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    dump("validated_pairs.jsonl", validated)
    dump("rejected_pairs.jsonl", rejected)
    dump("review_resolutions.jsonl", review_resolutions)
    dump("alternating_slide_pairs.jsonl", alternation)
    with open(PAIRS_DIR / "alternation_diagnostics.json", "w", encoding="utf-8") as fh:
        json.dump(alt_diagnostics, fh, indent=1)

    summary = {
        "auto_pairs_total": len(validated) + len(rejected),
        "validated": sum(1 for v in validated if v["status"] == "VALIDATED"),
        "partial": sum(1 for v in validated if v["status"] == "PARTIAL"),
        "golden_deck_pairs": len(validated),
        "golden_slide_pairs": sum(v["slide_alignment"]["matched"] for v in validated),
        "rejected": len(rejected),
        "review_resolved": sum(1 for r in review_resolutions if str(r["resolution"]).startswith(("RAW_", "CLEAN_"))),
        "review_weak_or_unresolved": sum(1 for r in review_resolutions if r["resolution"] in ("UNRESOLVED", "WEAK_MATCH_NEEDS_MANUAL")),
        "alternating_internal_pairs": len(alternation),
    }
    (config.METADATA_DIR / "pair_discovery_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def generate_report(validated, rejected, review_resolutions, alternation, alt_diag, summary) -> None:
    d = alt_diag
    lines = [
        "# MorphLite Pair Discovery Report",
        "",
        "| Stage | Count |",
        "|---|---|",
        f"| Golden deck pairs | {summary['golden_deck_pairs']} ({summary['validated']} validated / {summary['partial']} partial) |",
        f"| **Golden slide pairs** | **{summary['golden_slide_pairs']}** |",
        f"| Rejected | {summary['rejected']} |",
        f"| Review resolved | {summary['review_resolved']} |",
        f"| Review weak/unresolved | {summary['review_weak_or_unresolved']} |",
        f"| Alternating internal pairs | {summary['alternating_internal_pairs']} |",
        "",
        "## Alternation score distribution",
        "",
        f"Percentiles: `{d['candidate_score_percentiles']}`",
        "",
        "| Bucket | Candidates |",
        "|---|---|",
    ]
    lines += [f"| {k} | {v} |" for k, v in d["candidate_score_histogram"].items()]
    lines += [
        "",
        "## Validated deck pairs",
        "",
        "| Pair | Join | Slides | Content sim | Struct sim | Cov | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for v in sorted(validated, key=lambda x: -x["content_similarity"]):
        lines.append(
            f"| {v['name_key'][:38]} | {v['join_method']} | {v['slide_alignment']['matched']}/{max(v['slide_count_raw'], v['slide_count_branded'])} | {v['content_similarity']:.2f} | {v['structure_similarity']:.2f} | {v['coverage']:.0%} | {v['status']} |"
        )
    lines += ["", "## Alternation pairs", "", "| Deck | Slides | Dir | Sim | Margin |", "|---|---|---|---|---|"]
    for a in alternation:
        lines.append(f"| {a['deck_id'].split('__')[-1][:36]} | {a['slide_indices']} | {a['direction']} | {a['similarity']:.2f} | {a['margin']:.2f} |")
    (config.METADATA_DIR / "PAIR_DISCOVERY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    print("Loading manifests...", flush=True)
    manifest = load_ast_manifest()

    print("\n== Stage 1: validating auto-detected pairs ==", flush=True)
    validated, rejected = validate_auto_pairs(manifest)

    print("\n== Stage 2: resolving review decks ==", flush=True)
    review_res = resolve_review_decks(manifest)

    print("\n== Stage 3: Category B alternation scan ==", flush=True)
    alternation, alt_diag = detect_alternation(manifest)

    summary = write_outputs(validated, rejected, review_res, alternation, alt_diag)
    generate_report(validated, rejected, review_res, alternation, alt_diag, summary)
    print("\n" + json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
