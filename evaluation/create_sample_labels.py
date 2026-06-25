#!/usr/bin/env python3
"""
APTIVA AI — Sample Ground Truth Label Generator
================================================
Generates a bootstrapped ground truth CSV for the 50-candidate sample dataset
using a title-only heuristic that is completely independent of the scoring system.

Relevance scale:
  3 = Highly Relevant  — Senior/Staff/Lead/Principal AI/ML/NLP/Retrieval/Search Engineer
  2 = Relevant         — AI/ML/NLP Engineer, Applied Scientist, Data Scientist
  1 = Adjacent         — Software Engineer, Data Engineer, Backend, DevOps, PM
  0 = Not Relevant     — Civil, Mechanical, Accountant, HR, Marketing, etc.

IMPORTANT:
  These are bootstrap labels based on title matching only.
  They should be reviewed and corrected by a human domain expert before use
  as a definitive ground truth. The purpose is to provide a starting point,
  not a gold standard.

Usage:
  python evaluation/create_sample_labels.py
  # Creates: evaluation/sample_ground_truth.csv
"""

import json
import csv
import sys
from pathlib import Path

# Path resolution
SCRIPT_DIR   = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
SAMPLE_DATA  = PROJECT_ROOT / "data" / "sample_candidates.json"
OUTPUT_CSV   = SCRIPT_DIR / "sample_ground_truth.csv"


# ── Title-based relevance heuristic (independent of scorer) ─────────────────

TIER_3_KEYWORDS = [
    "senior ai engineer", "senior ml engineer", "senior machine learning engineer",
    "senior nlp engineer", "staff machine learning engineer", "staff ml engineer",
    "staff ai engineer", "lead ai engineer", "lead ml engineer",
    "principal ml engineer", "principal ai engineer",
    "senior applied scientist", "senior research engineer",
    "senior recommendation", "senior retrieval", "senior search",
    "senior data scientist",  # Senior DS with AI/ML context
]

TIER_2_KEYWORDS = [
    "ai engineer", "ml engineer", "machine learning engineer",
    "nlp engineer", "nlp researcher",
    "recommendation systems engineer", "recommender",
    "retrieval engineer", "search engineer", "search scientist",
    "applied ml engineer", "applied machine learning",
    "applied scientist", "research engineer", "research scientist",
    "llm engineer", "deep learning engineer", "computer vision engineer",
    "ai researcher", "ml researcher",
    "data scientist",  # Non-senior DS
]

TIER_1_KEYWORDS = [
    "software engineer", "software developer",
    "backend engineer", "backend developer",
    "data engineer", "platform engineer",
    "full stack", "fullstack",
    "devops engineer", "cloud engineer", "sre",
    "java developer", "python developer", ".net developer",
    "mobile developer", "android developer", "ios developer",
    "product manager", "program manager", "project manager",
    "business analyst", "qa engineer", "test engineer",
    "embedded engineer", "network engineer", "security engineer",
    "database administrator", "system administrator",
]

TIER_0_KEYWORDS = [
    "civil engineer", "mechanical engineer", "chemical engineer",
    "electrical engineer",  # low relevance unless embedded/signal
    "accountant", "finance", "chartered accountant",
    "hr manager", "human resources",
    "marketing manager", "marketing",
    "operations manager", "operations",
    "graphic designer", "designer",
    "customer support", "customer service",
    "content writer", "copywriter",
    "sales", "business development",
    "supply chain", "logistics",
    "teacher", "professor",
]


def title_to_relevance(title: str) -> int:
    """Map a job title to a relevance score using keyword heuristics."""
    t = title.lower().strip()

    # Check tier 3 first (most specific)
    for kw in TIER_3_KEYWORDS:
        if kw in t:
            return 3

    # Check tier 2
    for kw in TIER_2_KEYWORDS:
        if kw in t:
            return 2

    # Check tier 0 (explicit exclusions) before tier 1
    # to avoid "engineer" catch-all promoting civil engineers
    for kw in TIER_0_KEYWORDS:
        if kw in t:
            return 0

    # Check tier 1
    for kw in TIER_1_KEYWORDS:
        if kw in t:
            return 1

    # Unknown title — conservative default
    if "engineer" in t or "scientist" in t or "analyst" in t:
        return 1
    return 0


def main():
    if not SAMPLE_DATA.exists():
        print(f"Error: sample candidates not found at {SAMPLE_DATA}", file=sys.stderr)
        print("Run from project root: python evaluation/create_sample_labels.py",
              file=sys.stderr)
        sys.exit(1)

    with open(SAMPLE_DATA, encoding="utf-8") as f:
        raw = json.load(f)
    candidates = raw if isinstance(raw, list) else raw.get("candidates", [])

    rows = []
    for c in candidates:
        cid   = c.get("candidate_id", "")
        title = c.get("profile", {}).get("current_title", "")
        rel   = title_to_relevance(title)
        rows.append({
            "candidate_id": cid,
            "relevance":    rel,
            "title":        title,
            "note":         f"auto-labelled via title heuristic (REVIEW MANUALLY)",
        })

    # Sort by relevance descending for easy review
    rows.sort(key=lambda x: (-x["relevance"], x["candidate_id"]))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["candidate_id", "relevance", "title", "note"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} labels → {OUTPUT_CSV}")
    print()

    # Summary
    from collections import Counter
    dist = Counter(r["relevance"] for r in rows)
    for rel in (3, 2, 1, 0):
        label = {3: "Highly Relevant", 2: "Relevant      ",
                 1: "Adjacent       ", 0: "Not Relevant  "}[rel]
        print(f"  [{rel}] {label}: {dist.get(rel, 0):3d} candidates")

    print()
    print("IMPORTANT: Review and correct labels before using as ground truth.")
    print(f"Edit: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
