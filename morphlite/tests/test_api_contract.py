"""API contract test: verifies response schema and reconciliation invariants."""
import json
import os
import sys

sys.path.insert(0, "backend")
sys.path.insert(0, ".")


def main():
    from morphlite.pipeline.engine import BrandMorphPipeline
    import glob

    decks = sorted(glob.glob("data/source/paired/raw/**/*.pptx", recursive=True))
    if not decks:
        print("SKIP: no test decks found")
        return 0

    test_deck = decks[0]
    pipeline = BrandMorphPipeline()
    out = os.path.join(os.environ.get("TEMP", "/tmp"), "contract_test.pptx")
    result = pipeline.process(test_deck, out)
    d = result.to_json()

    errors = []

    totals = d.get("transformation_plan", {}).get("totals", {})
    bp = totals.get("by_policy", {})
    mv = totals.get("mutation_verification", {})
    nodes = totals.get("nodes_total", 0)

    # Invariant 1: policy sum == nodes_total
    policy_sum = sum(bp.values())
    if policy_sum != nodes:
        errors.append(f"policy_sum {policy_sum} != nodes_total {nodes}")

    # Invariant 2: no undefined/None in policy counts
    for k, v in bp.items():
        if v is None:
            errors.append(f"by_policy.{k} is None")

    # Invariant 3: mutation total <= apply count
    mv_total = sum(mv.values())
    apply_n = bp.get("APPLY", 0)
    if mv_total > apply_n:
        errors.append(f"mutation total {mv_total} > APPLY {apply_n}")

    # Invariant 4: per-slide reconciliation
    for s in d.get("slides", []):
        summary = s.get("summary", {})
        slide_total = summary.get("total", 0)
        parts = (summary.get("changed", 0) + summary.get("no_change", 0) +
                 summary.get("failed", 0) + summary.get("unsupported", 0) +
                 summary.get("review", 0) + summary.get("preserved", 0))
        if parts != slide_total:
            errors.append(f"slide {s['slide_number']}: parts {parts} != total {slide_total}")

    # Invariant 5: no None values in slide summaries
    for s in d.get("slides", []):
        for k, v in s.get("summary", {}).items():
            if v is None:
                errors.append(f"slide {s['slide_number']}: summary.{k} is None")

    # Invariant 6: required top-level keys exist
    for key in ("deck_id", "slides", "transformation_plan"):
        if key not in d:
            errors.append(f"missing top-level key: {key}")

    if errors:
        print("CONTRACT FAILURES:")
        for e in errors:
            print(f"  - {e}")
        print("API CONTRACT TEST FAILED")
        return 1

    print(f"API CONTRACT TEST PASSED ({nodes} nodes, {len(d.get('slides', []))} slides)")
    print(f"  by_policy: {bp}")
    print(f"  mutation_verification: {mv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
