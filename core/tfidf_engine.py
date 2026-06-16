"""
APTIVA AI — TF-IDF Engine
Builds and queries the TF-IDF index for career substance scoring.
Pre-computed ONCE per run; per-candidate query is a single dot product.
"""

from typing import List, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from core.jd_config import JD_CONFIG


def build_career_text(candidate: dict) -> str:
    """Concatenate all career history text for a candidate."""
    parts = []
    for job in candidate.get("career_history", []):
        desc = job.get("description", "")
        title = job.get("title", "")
        industry = job.get("industry", "")
        company = job.get("company", "")
        parts.append(f"{title} {company} {industry} {desc}")
    # Also include profile headline and summary
    profile = candidate.get("profile", {})
    parts.append(profile.get("headline", ""))
    parts.append(profile.get("summary", ""))
    return " ".join(parts)


def build_jd_text() -> str:
    """Build weighted JD text (repeat keywords to boost TF-IDF weight)."""
    keywords = JD_CONFIG["jd_career_keywords"]
    # Repeat × 5 to give JD keywords heavy weight
    return " ".join(keywords * 5)


def build_tfidf_index(
    candidates: List[dict],
    max_features: int = 8000,
    ngram_range: Tuple[int, int] = (1, 2),
    min_df: int = 2,
):
    """
    Build TF-IDF index for all candidates.

    Returns:
        vectorizer: Fitted TfidfVectorizer
        career_matrix: Sparse matrix (n_candidates × n_features)
        jd_vec: JD feature vector (1 × n_features)
        similarities: numpy array of cosine similarities (n_candidates,)
    """
    career_texts = [build_career_text(c) for c in candidates]
    jd_text = build_jd_text()

    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        min_df=min_df,
        strip_accents="unicode",
        lowercase=True,
        sublinear_tf=True,  # Apply log(1+tf) to reduce impact of high-frequency terms
    )

    # Fit on all texts including JD so JD terms are in vocabulary
    all_texts = career_texts + [jd_text]
    vectorizer.fit(all_texts)

    career_matrix = vectorizer.transform(career_texts)
    jd_vec = vectorizer.transform([jd_text])

    # Compute all similarities in one batch operation (very fast)
    similarities = cosine_similarity(jd_vec, career_matrix)[0]

    return vectorizer, career_matrix, jd_vec, similarities


def compute_skill_relevance_score(candidate: dict) -> float:
    """
    0.0–1.0 skill relevance score based on keyword overlap.
    Used in the hybrid career scoring formula:
        career_score = 0.7 × tfidf_similarity + 0.3 × skill_relevance
    """
    core_skills = [s.lower() for s in JD_CONFIG["core_skills"]]
    bonus_skills = [s.lower() for s in JD_CONFIG["bonus_skills"]]

    candidate_skills = [
        s.get("name", "").lower() for s in candidate.get("skills", [])
    ]
    career_text = build_career_text(candidate).lower()

    core_hits = 0
    bonus_hits = 0

    for skill in core_skills:
        if any(skill in cs or cs in skill for cs in candidate_skills) or skill in career_text:
            core_hits += 1

    for skill in bonus_skills:
        if any(skill in cs or cs in skill for cs in candidate_skills) or skill in career_text:
            bonus_hits += 1

    # Normalize
    core_score = min(1.0, core_hits / max(1, len(core_skills)))
    bonus_score = min(1.0, bonus_hits / max(1, len(bonus_skills)))

    return min(1.0, 0.75 * core_score + 0.25 * bonus_score)
