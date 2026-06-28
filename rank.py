#!/usr/bin/env python3
"""
APTIVA AI — Redrob Hackathon Ranking Engine
============================================
Primary deliverable for the India.Runs Data & AI Challenge.

Usage:
    python rank.py --candidates ./data/candidates.jsonl --out ./submission.xlsx
    python rank.py --candidates ./data/sample_candidates.json --out ./submission.xlsx
    python rank.py --candidates ./data/candidates.jsonl --out ./submission.xlsx --enrich-reasoning

Constraints:
    CPU only | <=5 min | <=16 GB RAM | no network during ranking

Architecture:
    1. Auto-detect dataset (ZIP extraction if needed)
    2. Load candidates (streaming JSONL or JSON array)
    3. Build TF-IDF index once (batch operation)
    4. Score all candidates (vectorized cosine + per-candidate rules)
    5. Select top-100 via heapq.nlargest (O(n log 100))
    6. Generate reasoning (template or precomputed)
    7. Write submission.xlsx
"""

import argparse
import csv
import heapq
import json
import sys
import time
from pathlib import Path

import yaml

# -- Import core modules -------------------------------------------------------
from core.dataset_loader import DatasetLoader
from core.reasoning import generate_reasoning
from core.scorer import compute_final_score
from core.tfidf_engine import build_tfidf_index


# -- Load configuration --------------------------------------------------------
def load_config(config_path: str = "config.yaml") -> dict:
    try:
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


# -- Main ranking pipeline -----------------------------------------------------
def rank_candidates(
    candidates_path: str,
    output_path: str,
    top_n: int = 100,
    config: dict = None,
    enrich_reasoning: bool = False,
) -> list:
    """
    Full ranking pipeline. Returns list of top-N scored candidates.

    Returns:
        list of (final_score, candidate, components) tuples
    """
    config = config or {}
    t_start = time.time()

    # -- Step 1: Load Candidates -------------------------------------------
    print("=" * 60)
    print("  APTIVA AI — Redrob Ranking Engine")
    print("=" * 60)

    loader = DatasetLoader(data_dir="./data")

    # Use provided path or auto-detect
    if candidates_path:
        target_path = Path(candidates_path)
    else:
        # Auto-setup (ZIP extraction if needed)
        status = loader.auto_setup()
        if not status["dataset_ready"]:
            print("[ERROR] No dataset found. Please place ZIP in data/ directory.")
            sys.exit(1)
        target_path = loader.get_candidates_path()

    print(f"  Loading candidates from: {target_path}", end="", flush=True)
    t0 = time.time()

    candidates = loader.load_all_candidates(target_path)
    print(f" [OK] {len(candidates):,} candidates loaded ({time.time() - t0:.1f}s)")

    if not candidates:
        print("[ERROR] No candidates loaded. Check the file path and format.")
        sys.exit(1)

    # -- Step 2: Build TF-IDF Index ----------------------------------------
    print(f"  Building TF-IDF index...", end="", flush=True)
    t0 = time.time()

    ranking_cfg = config.get("ranking", {})
    _, _, _, similarities = build_tfidf_index(
        candidates,
        max_features=ranking_cfg.get("tfidf_max_features", 8000),
        ngram_range=tuple(ranking_cfg.get("tfidf_ngram_range", [1, 2])),
        min_df=ranking_cfg.get("tfidf_min_df", 2),
    )
    print(f" [OK] done ({time.time() - t0:.1f}s)")

    # -- Step 3: Score All Candidates --------------------------------------
    print(f"  Scoring {len(candidates):,} candidates...", end="", flush=True)
    t0 = time.time()

    scored = []
    for i, candidate in enumerate(candidates):
        tfidf_sim = float(similarities[i])
        final_score, components = compute_final_score(candidate, tfidf_sim)
        scored.append((final_score, candidate, components))

    print(f" [OK] done ({time.time() - t0:.1f}s)")

    # -- Step 4: Select Top-N ----------------------------------------------
    print(f"  Selecting top {top_n}...")
    top_results = heapq.nlargest(top_n, scored, key=lambda x: x[0])
    top_results.sort(key=lambda x: (-x[0], x[1].get("candidate_id", "")))

    top_score = top_results[0][0] if top_results else 0
    bottom_score = top_results[-1][0] if top_results else 0
    print(f"  Score range: {top_score:.4f} -> {bottom_score:.4f}")

    # -- Step 5: Optional Gemini Enrichment -------------------------------
    if enrich_reasoning and config.get("enable_reasoning_enrichment", False):
        print("  Enriching reasoning with Gemini API (offline step)...")
        try:
            from core.gemini_enricher import enrich_reasonings
            top_entries = [
                {
                    "candidate_id": c["candidate_id"],
                    "rank": rank + 1,
                    "score": s,
                    "components": comp,
                }
                for rank, (s, c, comp) in enumerate(top_results)
            ]
            enrich_reasonings(
                candidates=candidates,
                top_scores=top_entries,
                gemini_model=config.get("gemini_model", "gemini-2.5-pro"),
                api_key=config.get("gemini_api_key", ""),
            )
        except Exception as e:
            print(f"  [WARN] Enrichment failed ({e}), using template reasoning")

    # -- Step 6: Write Submission XLSX --------------------------------------
    print(f"  Writing submission XLSX to: {output_path}")
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["candidate_id", "rank", "score", "reasoning"])

        for rank, (score, candidate, components) in enumerate(top_results, start=1):
            reasoning = generate_reasoning(
                candidate=candidate,
                rank=rank,
                components=components,
                use_precomputed=True,
            )
            writer.writerow([
                candidate["candidate_id"],
                rank,
                round(score, 4),
                reasoning,
            ])

    # -- Step 7: Summary ---------------------------------------------------
    total_time = time.time() - t_start
    print()
    print("=" * 60)
    print(f"  [OK] Submission written to: {out_path}")
    print(f"  [OK] Candidates ranked:     {len(candidates):,}")
    print(f"  [OK] Top score:             {top_score:.4f}")
    print(f"  [OK] Rank-100 score:        {bottom_score:.4f}")
    print(f"  [OK] Total runtime:         {total_time:.1f}s")
    print("=" * 60)

    # Print top 10 preview
    print("\n  TOP 10 CANDIDATES:")
    print(f"  {'Rank':<6} {'Candidate ID':<15} {'Score':<8} {'Hireability':<13} {'Title'}")
    print("  " + "-" * 70)
    for rank, (score, cand, comp) in enumerate(top_results[:10], start=1):
        hi = comp.get("hireability_index", {})
        hi_score = hi.get("overall", 0) if hi else 0
        title = cand["profile"].get("current_title", "Unknown")[:30]
        print(f"  {rank:<6} {cand['candidate_id']:<15} {score:<8.4f} {hi_score:<13.1f} {title}")

    return top_results


# -- Entry Point ---------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="APTIVA AI — Redrob Hackathon Candidate Ranker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rank.py --candidates data/candidates.jsonl --out submission.xlsx
  python rank.py --candidates data/sample_candidates.json --out submission.xlsx
  python rank.py --candidates data/candidates.jsonl --out submission.xlsx --enrich-reasoning
  python rank.py --auto                          # Auto-detect ZIP in data/
        """,
    )
    parser.add_argument("--candidates", help="Path to candidates.jsonl or sample_candidates.json")
    parser.add_argument("--out", default="submission.xlsx", help="Output CSV path")
    parser.add_argument("--top-n", type=int, default=100, help="Number of candidates to rank")
    parser.add_argument("--config", default="config.yaml", help="Config YAML path")
    parser.add_argument(
        "--enrich-reasoning",
        action="store_true",
        help="Run Gemini enrichment AFTER ranking (offline step, requires GEMINI_API_KEY)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect dataset ZIP in data/ directory",
    )

    args = parser.parse_args()
    config = load_config(args.config)

    candidates_path = args.candidates
    if args.auto or not candidates_path:
        loader = DatasetLoader(data_dir="./data")
        status = loader.auto_setup()
        if not status["dataset_ready"]:
            print("[ERROR] No dataset found. Place ZIP in data/ or use --candidates flag.")
            sys.exit(1)
        candidates_path = str(loader.get_candidates_path())
        print(f"  Auto-detected dataset: {candidates_path}")

    rank_candidates(
        candidates_path=candidates_path,
        output_path=args.out,
        top_n=args.top_n,
        config=config,
        enrich_reasoning=args.enrich_reasoning,
    )


if __name__ == "__main__":
    main()
