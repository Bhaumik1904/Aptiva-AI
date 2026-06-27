"""
APTIVA AI — Scoring Engine
All 7 component scoring functions + final score combiner.
Implements the hybrid career scoring: 0.7 x TF-IDF + 0.3 x Skill Relevance.
"""

from typing import Dict, Tuple

from core.behavioral import (
    compute_availability_score,
    compute_behavioral_multiplier,
    compute_trust_score,
    get_days_inactive,
)
from core.hireability import (
    compute_hireability_index,
    get_confidence_score,
    get_hire_recommendation,
    get_risk_score,
)
from core.honeypot import detect_honeypot
from core.jd_config import JD_CONFIG
from core.tfidf_engine import compute_skill_relevance_score

# -- Scoring Weights -----------------------------------------------------------
WEIGHTS = {
    "title":      0.30,
    "skills":     0.25,
    "career":     0.20,
    "experience": 0.10,
    "education":  0.05,
    "location":   0.05,
    "engagement": 0.05,
}


# -- Component 1: Title Match --------------------------------------------------

def score_title(candidate: Dict) -> float:
    """0.0–1.0. Title is the single most decisive filter."""
    title = candidate["profile"].get("current_title", "").lower().strip()
    title_scores = JD_CONFIG["title_scores"]

    best_score = 0.0
    matched = False  # Track whether any dict entry matched, even at score 0.0
    for jd_title, score in title_scores.items():
        if jd_title in title or title in jd_title:
            best_score = max(best_score, score)
            matched = True

    if not matched:
        # Catch-all: applies ONLY when no explicit entry matched.
        # Entries with score 0.0 in title_scores are intentional exclusions.
        if "engineer" in title or "scientist" in title:
            best_score = 0.25
        elif "analyst" in title or "developer" in title:
            best_score = 0.15
        else:
            best_score = 0.05

    return best_score


# -- Component 2: Skill Trust --------------------------------------------------

def score_skills(candidate: Dict) -> float:
    """0.0–1.0. Weighted by proficiency x endorsements x duration x assessment."""
    skills = candidate.get("skills", [])
    assessments = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})

    core_lower = [s.lower() for s in JD_CONFIG["core_skills"]]
    bonus_lower = [s.lower() for s in JD_CONFIG["bonus_skills"]]

    core_score = 0.0
    bonus_score = 0.0

    prof_weights = {"beginner": 0.25, "intermediate": 0.55, "advanced": 0.80, "expert": 1.0}

    for skill in skills:
        name = skill.get("name", "").lower()
        proficiency = skill.get("proficiency", "intermediate")
        endorsements = skill.get("endorsements", 0)
        duration = skill.get("duration_months", 0)

        prof_w = prof_weights.get(proficiency, 0.55)

        # Endorsement trust (log-ish, capped at 50)
        endorse_trust = min(1.0, (1 + endorsements) / 50)

        # Duration trust (capped at 36 months = 3 years)
        duration_trust = min(1.0, duration / 36)

        # Assessment score override
        for akey, aval in assessments.items():
            if akey.lower() in name or name in akey.lower():
                prof_w = 0.4 * prof_w + 0.6 * (aval / 100)
                break

        # Honeypot: expert with 0 duration
        if proficiency == "expert" and duration == 0:
            prof_w = 0.10

        trust_score = prof_w * (0.5 + 0.3 * endorse_trust + 0.2 * duration_trust)

        is_core = any(c in name or name in c for c in core_lower)
        is_bonus = any(b in name or name in b for b in bonus_lower) if not is_core else False

        if is_core:
            core_score = min(1.0, core_score + trust_score * 0.15)
        elif is_bonus:
            bonus_score = min(1.0, bonus_score + trust_score * 0.05)

    return min(1.0, 0.80 * core_score + 0.20 * bonus_score)


# -- Component 3: Career Substance (HYBRID) ------------------------------------

def score_career_substance(tfidf_similarity: float, candidate: Dict) -> float:
    """
    Hybrid career score:
        career_score = 0.7 x TF-IDF Similarity + 0.3 x Skill Relevance Score

    Also applies:
    - Consulting-firm penalty
    - Product-company bonus
    """
    # Skill relevance component
    skill_relevance = compute_skill_relevance_score(candidate)

    # Hybrid combination
    hybrid_score = 0.70 * tfidf_similarity + 0.30 * skill_relevance

    # Consulting-only penalty
    career = candidate.get("career_history", [])
    if career:
        consulting_ratio = sum(
            1 for job in career
            if any(firm in job.get("company", "").lower() for firm in JD_CONFIG["consulting_firms"])
        ) / len(career)
    else:
        consulting_ratio = 0.0

    consulting_penalty = consulting_ratio * 0.30

    # Product company bonus
    industries = [job.get("industry", "").lower() for job in career]
    is_product = any(
        ind in JD_CONFIG["preferred_industries"] for ind in industries
    )
    product_bonus = 0.08 if is_product else 0.0

    return min(1.0, max(0.0, hybrid_score + product_bonus - consulting_penalty))


# -- Component 4: Experience Window --------------------------------------------

def score_experience(candidate: Dict) -> float:
    """0.0–1.0. Optimal: 6–8 years. JD target: 5–9."""
    yoe = candidate["profile"].get("years_of_experience", 0)
    if 6 <= yoe <= 8:
        return 1.0
    elif 5 <= yoe < 6 or 8 < yoe <= 9:
        return 0.85
    elif 4 <= yoe < 5:
        return 0.65
    elif 9 < yoe <= 12:
        return 0.75
    elif 12 < yoe <= 15:
        return 0.55
    elif yoe > 15:
        return 0.35
    else:  # < 4 years
        return max(0.0, yoe / 4 * 0.50)


# -- Component 5: Education ----------------------------------------------------

def score_education(candidate: Dict) -> float:
    """0.0–1.0. Best degree wins (not averaged)."""
    education = candidate.get("education", [])
    if not education:
        return 0.30

    tier_scores = {"tier_1": 1.0, "tier_2": 0.78, "tier_3": 0.58, "tier_4": 0.42, "unknown": 0.48}
    degree_scores = {
        "ph.d": 1.0, "phd": 1.0, "d.phil": 1.0,
        "m.tech": 0.90, "m.e.": 0.88, "m.s.": 0.85, "ms": 0.85,
        "m.sc": 0.80, "msc": 0.80,
        "b.tech": 0.75, "b.e.": 0.75, "be": 0.75, "btech": 0.75,
        "b.sc": 0.65, "bsc": 0.65,
        "mba": 0.52,
    }
    field_kws = [
        "computer science", "computer engineering", "information technology",
        "electrical", "mathematics", "data science", "artificial intelligence",
        "statistics", "electronics", "machine learning",
    ]

    best = 0.0
    for edu in education:
        tier = edu.get("tier", "unknown")
        degree = edu.get("degree", "").lower()
        field = edu.get("field_of_study", "").lower()

        tier_s = tier_scores.get(tier, 0.48)
        degree_s = max(
            (v for k, v in degree_scores.items() if k in degree), default=0.50
        )
        field_bonus = 0.10 if any(kw in field for kw in field_kws) else 0.0

        score = 0.60 * tier_s + 0.30 * degree_s + field_bonus
        best = max(best, score)

    return min(1.0, best)


# -- Component 6: Location -----------------------------------------------------

def score_location(candidate: Dict) -> float:
    """0.0–1.0. JD prefers Pune/Noida/Delhi NCR/Hyderabad/Mumbai/Bangalore."""
    location = candidate["profile"].get("location", "").lower()
    country = candidate["profile"].get("country", "").lower()
    willing = candidate.get("redrob_signals", {}).get("willing_to_relocate", False)

    preferred = JD_CONFIG["preferred_locations"]
    if any(loc in location for loc in preferred):
        return 1.0
    elif "india" in country or country == "in":
        return 0.80 if willing else 0.50
    else:
        return 0.40 if willing else 0.15


# -- Engagement Base -----------------------------------------------------------

def score_engagement_base(candidate: Dict) -> float:
    """0.0–1.0. Simple engagement signal for the base weighted score."""
    signals = candidate.get("redrob_signals", {})
    pcs = signals.get("profile_completeness_score", 50) / 100
    otw = int(signals.get("open_to_work_flag", False))
    rr = signals.get("recruiter_response_rate", 0.5)
    return min(1.0, 0.30 * pcs + 0.30 * otw + 0.40 * rr)


# -- Final Score Combiner ------------------------------------------------------

def compute_final_score(candidate: Dict, tfidf_similarity: float) -> Tuple[float, Dict]:
    """
    Full scoring pipeline for one candidate.

    Returns:
        (final_score, components_dict)
    """
    # Honeypot check first
    is_honeypot, hp_flags = detect_honeypot(candidate)
    if is_honeypot:
        return 0.001, {
            "honeypot": True,
            "honeypot_flags": hp_flags,
            "final_score": 0.001,
        }

    signals = candidate.get("redrob_signals", {})

    # Component scores
    title_s      = score_title(candidate)
    skills_s     = score_skills(candidate)
    career_s     = score_career_substance(tfidf_similarity, candidate)
    experience_s = score_experience(candidate)
    education_s  = score_education(candidate)
    location_s   = score_location(candidate)
    engagement_s = score_engagement_base(candidate)

    # Behavioral sub-scores
    behavioral_mult = compute_behavioral_multiplier(candidate)
    availability_s  = compute_availability_score(signals)
    trust_s         = compute_trust_score(candidate)

    # Weighted base score
    base_score = (
        WEIGHTS["title"]      * title_s
        + WEIGHTS["skills"]     * skills_s
        + WEIGHTS["career"]     * career_s
        + WEIGHTS["experience"] * experience_s
        + WEIGHTS["education"]  * education_s
        + WEIGHTS["location"]   * location_s
        + WEIGHTS["engagement"] * engagement_s
    )

    # Apply behavioral multiplier
    final_score = min(1.0, base_score * behavioral_mult)

    # -- Relevance Gate --------------------------------------------------------
    # Prevents candidates with no AI/ML title, skills, or career evidence from
    # outranking legitimate tech candidates via domain-agnostic signals alone
    # (experience window, location, education tier, engagement).
    #
    # domain_rel: normalised combined weight of the three domain-aware components.
    # Threshold 0.01 chosen from calibration study — sits in the natural gap
    # between 0.0055 (last irrelevant candidate) and 0.0229 (first software role).
    # Precision: 100% (zero collateral on any legitimate tech/software candidate).
    _domain_weight = WEIGHTS["title"] + WEIGHTS["skills"] + WEIGHTS["career"]
    domain_rel = (
        WEIGHTS["title"]  * title_s
        + WEIGHTS["skills"] * skills_s
        + WEIGHTS["career"] * career_s
    ) / _domain_weight
    if domain_rel < 0.01:
        final_score = min(0.15, final_score)

    # Build full components dict
    components = {
        "title":               round(title_s, 4),
        "skills":              round(skills_s, 4),
        "career":              round(career_s, 4),
        "experience":          round(experience_s, 4),
        "education":           round(education_s, 4),
        "location":            round(location_s, 4),
        "engagement":          round(engagement_s, 4),
        "behavioral_multiplier": round(behavioral_mult, 4),
        "availability":        round(availability_s, 4),
        "trust_score":         round(trust_s, 4),
        "base_score":          round(base_score, 4),
        "final_score":         round(final_score, 4),
        "domain_relevance":    round(domain_rel, 4),   # gate diagnostic field
        "relevance_gated":     domain_rel < 0.01,      # True if gate fired
        "honeypot":            False,
        "honeypot_flags":      [],
    }

    # Hireability Index
    hi = compute_hireability_index(components)
    components["hireability_index"] = hi

    # Auxiliary scores
    recommendation = get_hire_recommendation(hi["overall"], final_score)
    # Relevance gate override: if gate fired, candidate cannot receive a positive label.
    # Ensures rank order and recommendation badge are always consistent.
    if components.get("relevance_gated", False):
        recommendation = "NO"
    confidence = get_confidence_score(components, is_honeypot=False)
    risk = get_risk_score(candidate, components, [])

    components["recommendation"]   = recommendation
    components["confidence_score"] = confidence
    components["risk_score"]       = risk

    return final_score, components
