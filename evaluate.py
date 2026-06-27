#!/usr/bin/env python3
"""
APTIVA AI — Ranking Evaluation Framework
=========================================
Computes standard IR ranking metrics against a ground-truth label file.

Metrics:
  NDCG@10   — Primary evaluation metric (50% of challenge score)
  NDCG@50   — Secondary metric (30%)
  MAP       — Mean Average Precision (15%)
  P@10      — Precision at 10 (5%)

Usage:
  python evaluate.py --predictions submission.csv \\
                     --ground-truth evaluation/sample_ground_truth.csv

  python evaluate.py --predictions submission.csv \\
                     --ground-truth ground_truth.csv \\
                     --out evaluation/report.txt \\
                     --verbose
"""

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# -- Relevance Scale ------------------------------------------------------------
RELEVANCE_LABELS = {
    0: "Not Relevant  (non-AI/ML profile, honeypot, trap)",
    1: "Adjacent      (technical but not AI/ML core)",
    2: "Relevant      (AI/ML engineer, meets most JD criteria)",
    3: "Highly Relevant (exact JD match, senior AI/ML engineer)",
}
RELEVANT_THRESHOLD = 1  # rel >= 1 is considered a "relevant" document for MAP/P@K


# -- Core Metric Implementations -----------------------------------------------

def dcg_at_k(relevances: List[float], k: int) -> float:
    """
    Discounted Cumulative Gain at rank K.
    Uses the standard formula: sum((2^rel - 1) / log2(rank + 1))
    """
    gain = 0.0
    for i, rel in enumerate(relevances[:k]):
        gain += (2 ** rel - 1) / math.log2(i + 2)  # i+2 because i is 0-indexed
    return gain


def ndcg_at_k(relevances: List[float], k: int) -> float:
    """
    Normalised DCG at rank K.
    Divides actual DCG by ideal DCG (best possible ranking of the same labels).
    Returns 0.0 if there are no relevant documents.
    """
    actual_dcg = dcg_at_k(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    ideal_dcg = dcg_at_k(ideal_relevances, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0.0 else 0.0


def average_precision(relevances: List[float], threshold: int = RELEVANT_THRESHOLD) -> float:
    """
    Average Precision (AP) for a single ranked list.
    Computes precision at each position where a relevant document appears,
    then averages over all relevant documents.
    Returns 0.0 if no relevant documents exist.
    """
    hits = 0
    precision_sum = 0.0
    total_relevant = sum(1 for r in relevances if r >= threshold)

    if total_relevant == 0:
        return 0.0

    for i, rel in enumerate(relevances):
        if rel >= threshold:
            hits += 1
            precision_sum += hits / (i + 1)

    return precision_sum / total_relevant


def precision_at_k(relevances: List[float], k: int,
                   threshold: int = RELEVANT_THRESHOLD) -> float:
    """
    Precision at rank K.
    Fraction of the top-K retrieved documents that are relevant.
    """
    top_k = relevances[:k]
    if not top_k:
        return 0.0
    return sum(1 for r in top_k if r >= threshold) / len(top_k)


def recall_at_k(relevances: List[float], k: int,
                threshold: int = RELEVANT_THRESHOLD) -> float:
    """
    Recall at rank K.
    Fraction of all relevant documents that appear in the top-K.
    """
    total_relevant = sum(1 for r in relevances if r >= threshold)
    if total_relevant == 0:
        return 0.0
    retrieved_relevant = sum(1 for r in relevances[:k] if r >= threshold)
    return retrieved_relevant / total_relevant


def mean_reciprocal_rank(relevances: List[float],
                         threshold: int = RELEVANT_THRESHOLD) -> float:
    """
    Mean Reciprocal Rank (MRR).
    Reciprocal of the rank of the first relevant document.
    """
    for i, rel in enumerate(relevances):
        if rel >= threshold:
            return 1.0 / (i + 1)
    return 0.0


# -- I/O -----------------------------------------------------------------------

def load_predictions(csv_path: str) -> List[Tuple[int, str, float]]:
    """
    Load predictions CSV.
    Returns list of (rank, candidate_id, score) sorted by rank ascending.
    Expected format: candidate_id, rank, score, reasoning
    """
    rows = []
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {csv_path}")

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rank = int(row["rank"].strip())
                cid  = row["candidate_id"].strip()
                score = float(row["score"].strip())
                rows.append((rank, cid, score))
            except (KeyError, ValueError) as e:
                raise ValueError(f"Malformed predictions row: {row} — {e}")

    rows.sort(key=lambda x: x[0])
    return rows


def load_ground_truth(csv_path: str) -> Dict[str, int]:
    """
    Load ground truth labels.
    Returns dict: candidate_id -> relevance (integer 0–3).
    Expected format: candidate_id, relevance
    """
    labels = {}
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {csv_path}")

    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cid = row["candidate_id"].strip()
                rel = int(row["relevance"].strip())
                if rel not in (0, 1, 2, 3):
                    raise ValueError(f"Relevance must be 0–3, got {rel}")
                labels[cid] = rel
            except (KeyError, ValueError) as e:
                raise ValueError(f"Malformed ground truth row: {row} — {e}")

    return labels


# -- Evaluation Engine ---------------------------------------------------------

def evaluate(predictions: List[Tuple[int, str, float]],
             ground_truth: Dict[str, int],
             k_values: Tuple[int, ...] = (10, 50),
             verbose: bool = False) -> Dict:
    """
    Run all evaluation metrics.

    Args:
        predictions: List of (rank, candidate_id, score) sorted by rank.
        ground_truth: Dict mapping candidate_id -> relevance score.
        k_values: Tuple of K values for NDCG and other @K metrics.
        verbose: If True, print per-candidate details.

    Returns:
        Dict with all metric results and metadata.
    """
    # Build ranked relevance list (use 0 for candidates not in ground truth)
    ranked_relevances = []
    ranked_cids = []
    unlabelled = []

    for rank, cid, score in predictions:
        if cid in ground_truth:
            rel = ground_truth[cid]
        else:
            rel = 0  # Conservative: unlabelled = not relevant
            unlabelled.append((rank, cid))
        ranked_relevances.append(rel)
        ranked_cids.append((rank, cid, rel))

    if verbose and unlabelled:
        print(f"\n  [WARNING] {len(unlabelled)} predicted candidates have no ground truth label.")
        print(f"  They are treated as relevance=0 (conservative).")
        for rank, cid in unlabelled[:10]:
            print(f"    Rank #{rank:3d}  {cid}")
        if len(unlabelled) > 10:
            print(f"    ... and {len(unlabelled) - 10} more")

    # All relevant candidates in ground truth (for recall calculation)
    all_relevant = sum(1 for r in ground_truth.values() if r >= RELEVANT_THRESHOLD)

    results = {
        "n_predictions": len(predictions),
        "n_ground_truth": len(ground_truth),
        "n_unlabelled":   len(unlabelled),
        "n_relevant_in_gt": all_relevant,
        "metrics": {},
    }

    # Per-candidate verbose output
    if verbose:
        print(f"\n{'-'*75}")
        print(f"  {'Rank':>4}  {'Candidate':<15}  {'Score':>7}  {'Relevance':>10}  Label")
        print(f"{'-'*75}")
        for rank, cid, rel in ranked_cids[:max(k_values)]:
            label = RELEVANCE_LABELS.get(rel, "?")
            marker = "[OK]" if rel >= RELEVANT_THRESHOLD else "[FAIL]"
            print(f"  {rank:4d}  {cid:<15}  {predictions[rank-1][2]:7.4f}  "
                  f"{rel:>10}  {marker} {label}")
        print(f"{'-'*75}")

    # Compute NDCG@K for each K
    for k in k_values:
        ndcg = ndcg_at_k(ranked_relevances, k)
        p_k  = precision_at_k(ranked_relevances, k)
        r_k  = recall_at_k(ranked_relevances, k)
        results["metrics"][f"NDCG@{k}"]      = ndcg
        results["metrics"][f"Precision@{k}"] = p_k
        results["metrics"][f"Recall@{k}"]    = r_k

    # MAP over full ranked list
    results["metrics"]["MAP"] = average_precision(ranked_relevances)

    # MRR
    results["metrics"]["MRR"] = mean_reciprocal_rank(ranked_relevances)

    # Relevance distribution in top-10 and top-50
    for k in k_values:
        dist = {0: 0, 1: 0, 2: 0, 3: 0}
        for rel in ranked_relevances[:k]:
            dist[rel] = dist.get(rel, 0) + 1
        results[f"relevance_dist@{k}"] = dist

    return results


# -- Report Formatter ----------------------------------------------------------

def format_report(results: Dict,
                  predictions_path: str,
                  ground_truth_path: str,
                  k_values: Tuple[int, ...]) -> str:
    """Format the evaluation results into a human-readable report."""
    lines = []
    lines.append("=" * 65)
    lines.append("  APTIVA AI — RANKING EVALUATION REPORT")
    lines.append("=" * 65)
    lines.append(f"  Predictions : {predictions_path}")
    lines.append(f"  Ground truth: {ground_truth_path}")
    lines.append(f"  Ranked candidates : {results['n_predictions']}")
    lines.append(f"  Labelled in GT    : {results['n_ground_truth']}")
    lines.append(f"  Unlabelled (-> 0)  : {results['n_unlabelled']}")
    lines.append(f"  Relevant in GT    : {results['n_relevant_in_gt']}")
    lines.append("")

    # Primary metrics table (matching challenge evaluation criteria)
    lines.append("-" * 65)
    lines.append("  PRIMARY METRICS  (challenge evaluation criteria)")
    lines.append("-" * 65)

    m = results["metrics"]

    challenge_metrics = [
        ("NDCG@10",      m.get("NDCG@10", 0),      "50%", "Primary criterion"),
        ("NDCG@50",      m.get("NDCG@50", 0),       "30%", "Secondary criterion"),
        ("MAP",          m.get("MAP",     0),        "15%", "Precision across all ranks"),
        ("Precision@10", m.get("Precision@10", 0),   "5%", "Top-10 precision"),
    ]

    for metric, value, weight, note in challenge_metrics:
        bar_len = int(value * 30)
        bar = "#" * bar_len + "-" * (30 - bar_len)
        lines.append(f"  {metric:<14} {value:6.4f}  [{bar}]  (weight {weight})  {note}")

    lines.append("")
    lines.append("-" * 65)
    lines.append("  ADDITIONAL METRICS")
    lines.append("-" * 65)

    additional = [
        ("MRR",           m.get("MRR",           0), "Mean Reciprocal Rank"),
        ("Recall@10",     m.get("Recall@10",      0), "Fraction of relevant docs in top-10"),
        ("Recall@50",     m.get("Recall@50",      0), "Fraction of relevant docs in top-50"),
        ("Precision@50",  m.get("Precision@50",   0), "Top-50 precision"),
    ]

    for metric, value, note in additional:
        lines.append(f"  {metric:<14} {value:6.4f}    {note}")

    lines.append("")
    lines.append("-" * 65)
    lines.append("  RELEVANCE DISTRIBUTION")
    lines.append("-" * 65)

    for k in k_values:
        dist = results.get(f"relevance_dist@{k}", {})
        total = sum(dist.values())
        lines.append(f"  Top-{k} relevance breakdown:")
        for rel in (3, 2, 1, 0):
            count = dist.get(rel, 0)
            pct   = count / total * 100 if total else 0
            label = {3: "Highly Relevant", 2: "Relevant      ",
                     1: "Adjacent       ", 0: "Not Relevant  "}[rel]
            lines.append(f"    [{rel}] {label} : {count:3d}  ({pct:5.1f}%)")
        lines.append("")

    lines.append("-" * 65)
    lines.append("  SCORE INTERPRETATION")
    lines.append("-" * 65)

    ndcg10 = m.get("NDCG@10", 0)
    if ndcg10 >= 0.90:
        interpretation = "Excellent — ranking closely matches expert judgement"
    elif ndcg10 >= 0.75:
        interpretation = "Strong — ordering is mostly correct with minor discrepancies"
    elif ndcg10 >= 0.60:
        interpretation = "Adequate — correct candidates, some ordering issues"
    elif ndcg10 >= 0.40:
        interpretation = "Moderate — some relevant candidates ranked too low"
    else:
        interpretation = "Weak — significant ordering problems detected"

    lines.append(f"  NDCG@10 = {ndcg10:.4f} -> {interpretation}")
    lines.append("")
    lines.append("  Relevance scale used:")
    for rel, desc in RELEVANCE_LABELS.items():
        lines.append(f"    [{rel}] {desc}")
    lines.append(f"  Threshold for 'relevant': rel >= {RELEVANT_THRESHOLD} (used in MAP, P@K, MRR)")
    lines.append("")
    lines.append("=" * 65)

    return "\n".join(lines)


# -- CLI -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="APTIVA AI — Ranking Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate submission against sample labels
  python evaluate.py --predictions submission.csv \\
                     --ground-truth evaluation/sample_ground_truth.csv

  # Custom K values with verbose per-candidate output
  python evaluate.py --predictions submission.csv \\
                     --ground-truth evaluation/sample_ground_truth.csv \\
                     --k 10 25 50 --verbose

  # Save report to file
  python evaluate.py --predictions submission.csv \\
                     --ground-truth evaluation/sample_ground_truth.csv \\
                     --out evaluation/report.txt
        """
    )

    parser.add_argument(
        "--predictions", "-p",
        required=True,
        help="Path to predictions CSV (candidate_id, rank, score, reasoning)"
    )
    parser.add_argument(
        "--ground-truth", "-g",
        required=True,
        dest="ground_truth",
        help="Path to ground truth CSV (candidate_id, relevance)"
    )
    parser.add_argument(
        "--k", "-k",
        nargs="+",
        type=int,
        default=[10, 50],
        metavar="K",
        help="K values for @K metrics (default: 10 50)"
    )
    parser.add_argument(
        "--out", "-o",
        help="Optional: save report to this file path"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print per-candidate relevance breakdown"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Also output raw metrics as JSON to stdout"
    )

    args = parser.parse_args()
    k_values = tuple(sorted(set(args.k)))

    # Load data
    try:
        predictions  = load_predictions(args.predictions)
        ground_truth = load_ground_truth(args.ground_truth)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not predictions:
        print("Error: predictions file is empty.", file=sys.stderr)
        sys.exit(1)

    if not ground_truth:
        print("Error: ground truth file is empty.", file=sys.stderr)
        sys.exit(1)

    # Run evaluation
    results = evaluate(predictions, ground_truth, k_values=k_values,
                       verbose=args.verbose)

    # Format and print report
    report = format_report(results, args.predictions, args.ground_truth, k_values)
    print(report)

    # Optionally save to file
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"\n  Report saved to: {args.out}")

    # Optionally output JSON
    if args.json:
        import json
        print("\n  JSON metrics:")
        print(json.dumps(results["metrics"], indent=4))


if __name__ == "__main__":
    main()
