"""
APTIVA AI — Gemini Reasoning Enricher
OPTIONAL OFFLINE STEP. Never called during ranking.

Workflow:
  1. Run rank.py -> get top-100 candidates
  2. Run: python enrich_reasoning.py --submission submission.csv --candidates data/sample_candidates.json
  3. Enriched reasoning saved to precomputed_reasonings.json
  4. On next rank.py run, reasoning.py auto-loads the enriched file

The ranker NEVER depends on Gemini. This is purely a quality improvement step.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

PRECOMPUTED_PATH = Path("precomputed_reasonings.json")


def enrich_reasonings(
    candidates: List[Dict],
    top_scores: List[Dict],
    gemini_model: str = "gemini-2.5-pro",
    api_key: Optional[str] = None,
    output_path: Path = PRECOMPUTED_PATH,
) -> Dict[str, str]:
    """
    Use Gemini API to generate high-quality reasoning for top-100 candidates.

    Args:
        candidates: list of candidate dicts (must include candidate_id)
        top_scores: list of {candidate_id, rank, score, components} dicts
        gemini_model: Gemini model name
        api_key: Gemini API key (falls back to GEMINI_API_KEY env var)
        output_path: where to save precomputed_reasonings.json

    Returns:
        dict mapping candidate_id -> enriched_reasoning_string
    """
    try:
        import google.generativeai as genai
    except ImportError:
        print("google-generativeai not installed. Run: pip install google-generativeai")
        return {}

    # Configure API
    key = api_key or os.environ.get("GEMINI_API_KEY", "")
    if not key:
        print("GEMINI_API_KEY not set. Set it as an environment variable.")
        return {}

    genai.configure(api_key=key)
    model = genai.GenerativeModel(gemini_model)

    # Index candidates by ID
    cand_index = {c["candidate_id"]: c for c in candidates}

    enriched: Dict[str, str] = {}

    # Load existing to resume interrupted runs
    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            enriched = json.load(f)

    print(f"Enriching reasoning for {len(top_scores)} candidates using {gemini_model}...")

    for i, entry in enumerate(top_scores):
        cid = entry["candidate_id"]
        rank = entry["rank"]
        score = entry["score"]

        # Skip if already enriched
        if cid in enriched:
            print(f"  [{i+1}/{len(top_scores)}] {cid} — already enriched, skipping")
            continue

        candidate = cand_index.get(cid)
        if not candidate:
            continue

        prompt = _build_prompt(candidate, rank, score, entry.get("components", {}))

        try:
            response = model.generate_content(prompt)
            reasoning = response.text.strip()
            # Truncate to 500 chars max (submission spec limit)
            reasoning = reasoning[:500]
            enriched[cid] = reasoning
            print(f"  [{i+1}/{len(top_scores)}] {cid} rank #{rank} — enriched")
        except Exception as e:
            print(f"  [{i+1}/{len(top_scores)}] {cid} — API error: {e}, using template")
            # Don't add to enriched — will fall back to template

        # Rate limiting: 60 RPM for Gemini
        time.sleep(1.0)

        # Save incrementally to survive interruptions
        if (i + 1) % 10 == 0:
            _save(enriched, output_path)

    _save(enriched, output_path)
    print(f"[OK] Enriched {len(enriched)} reasonings saved to {output_path}")
    return enriched


def _build_prompt(candidate: Dict, rank: int, score: float, components: Dict) -> str:
    """Build a precise prompt for Gemini to generate candidate reasoning."""
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    skills = [s.get("name") for s in candidate.get("skills", [])[:8]]
    career_titles = [job.get("title") for job in candidate.get("career_history", [])[:3]]
    hi = components.get("hireability_index", {})

    return f"""You are a senior technical recruiter at Redrob AI evaluating candidates for a Senior AI Engineer role.

The role requires: production embeddings/retrieval systems, vector databases (FAISS, Pinecone), Python, NLP, evaluation frameworks (NDCG, MRR), 5-9 years experience, product company background.

Candidate summary:
- Title: {profile.get('current_title')}
- Company: {profile.get('current_company')}
- Experience: {profile.get('years_of_experience')} years
- Location: {profile.get('location')}
- Skills: {', '.join(skills)}
- Past roles: {', '.join(career_titles)}
- Notice period: {signals.get('notice_period_days')} days
- Open to work: {signals.get('open_to_work_flag')}
- Hireability Index: {hi.get('overall', 'N/A')}/100
- Overall score: {score:.3f}
- Rank: #{rank} of 100

Write a 1-2 sentence recruiter reasoning for this candidate. Be specific (mention actual skills, years, companies). Be honest about strengths AND concerns. Do not hallucinate. Maximum 120 words."""


def _save(enriched: Dict, path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)
