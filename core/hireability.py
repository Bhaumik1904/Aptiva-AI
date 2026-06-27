"""
APTIVA AI — Hireability Index
Proprietary single-score trust metric for recruiters.

Formula:
  Technical Fit     35%  (title 40% + skills 60%)
  Career Relevance  25%  (hybrid TF-IDF + skill relevance)
  Behavior Signals  20%  (behavioral multiplier normalized to 0-100)
  Availability      10%  (notice + last active + open-to-work)
  Trust Score       10%  (verifications + completeness + assessments)

Output: dict with 'overall' (0-100) and 5 sub-scores (0-100)
"""

from typing import Dict


# Hireability weights (must sum to 1.0)
HI_WEIGHTS = {
    "technical_fit": 0.35,
    "career_relevance": 0.25,
    "behavior_signals": 0.20,
    "availability": 0.10,
    "trust_score": 0.10,
}


def compute_hireability_index(components: Dict) -> Dict[str, float]:
    """
    Compute the Hireability Index from scoring components.

    Args:
        components: dict containing all scoring outputs:
            - title (0-1)
            - skills (0-1)
            - career (0-1)
            - behavioral_multiplier (0.75-1.15, System B clamped range)
            - availability (0-1)  ← from behavioral.compute_availability_score
            - trust_score (0-1)   ← from behavioral.compute_trust_score

    Returns:
        dict: {
            "overall": 0-100,
            "technical_fit": 0-100,
            "career_relevance": 0-100,
            "behavior_signals": 0-100,
            "availability": 0-100,
            "trust_score": 0-100,
        }
    """
    # Technical Fit: 40% title + 60% skills
    technical_fit = min(1.0, 0.40 * components.get("title", 0) + 0.60 * components.get("skills", 0))

    # Career Relevance: direct career substance score
    career_relevance = min(1.0, components.get("career", 0))

    # Behavior Signals: normalize behavioral multiplier -> (0–1)
    # Range updated to [0.75, 1.15] to match the System B BM clamp in behavioral.py.
    # Old range [0.10, 1.25] caused a permanent floor of 56.5% behavior_signals
    # for every candidate (BM never goes below 0.75 post-clamp).
    bm = components.get("behavioral_multiplier", 1.0)
    bm_min, bm_max = 0.75, 1.15   # System B live range
    behavior_signals = min(1.0, max(0.0, (bm - bm_min) / (bm_max - bm_min)))

    # Availability & Trust from pre-computed sub-scores
    availability = min(1.0, components.get("availability", 0.5))
    trust = min(1.0, components.get("trust_score", 0.5))

    # Weighted sum -> 0-100
    overall = (
        HI_WEIGHTS["technical_fit"]    * technical_fit
        + HI_WEIGHTS["career_relevance"]  * career_relevance
        + HI_WEIGHTS["behavior_signals"]  * behavior_signals
        + HI_WEIGHTS["availability"]      * availability
        + HI_WEIGHTS["trust_score"]       * trust
    ) * 100

    return {
        "overall":          round(min(100.0, max(0.0, overall)), 1),
        "technical_fit":    round(technical_fit * 100, 1),
        "career_relevance": round(career_relevance * 100, 1),
        "behavior_signals": round(behavior_signals * 100, 1),
        "availability":     round(availability * 100, 1),
        "trust_score":      round(trust * 100, 1),
    }


def get_hire_recommendation(hi_score: float, final_score: float) -> str:
    """Map Final Score + Hireability Index to a hire recommendation label.

    Final Score is the PRIMARY gate; HI is the confirming signal.
    All tiers use AND — HI alone cannot promote a low-scoring candidate.
    This ensures recommendation labels are always consistent with rank order.

    Thresholds calibrated to the live HI distribution (observed max ~ 64
    for the top AI candidate in a mixed-role dataset):

      STRONG_YES: FS >= 0.75 AND HI >= 60  (elite AI fit + strong HI)
      YES:        FS >= 0.35 AND HI >= 35  (solid AI fit confirmed by HI)
      MAYBE:      FS >= 0.18 AND HI >= 20  (meaningful signal, worth review)
      NO:         everything else
    """
    if final_score >= 0.75 and hi_score >= 60:
        return "STRONG_YES"
    elif final_score >= 0.35 and hi_score >= 35:
        return "YES"
    elif final_score >= 0.18 and hi_score >= 20:
        return "MAYBE"
    else:
        return "NO"



def get_confidence_score(components: Dict, is_honeypot: bool) -> float:
    """
    0.0–1.0 confidence in the overall ranking decision.
    Higher when multiple strong signals agree.
    """
    if is_honeypot:
        return 0.05

    signals_present = sum([
        1 if components.get("title", 0) > 0.5 else 0,
        1 if components.get("skills", 0) > 0.4 else 0,
        1 if components.get("career", 0) > 0.4 else 0,
        1 if components.get("trust_score", 0) > 0.5 else 0,
        1 if components.get("availability", 0) > 0.4 else 0,
    ])

    base_confidence = signals_present / 5.0
    # Boost confidence if title and skills both agree
    if components.get("title", 0) > 0.7 and components.get("skills", 0) > 0.6:
        base_confidence = min(1.0, base_confidence + 0.15)

    return round(base_confidence, 2)


def get_risk_score(candidate: Dict, components: Dict, honeypot_flags: list) -> float:
    """
    0.0–1.0 risk score (higher = riskier hire).
    Based on: honeypot flags, ghost signals, consulting-only, high notice.
    """
    risk = 0.0

    # Honeypot flags
    if honeypot_flags:
        risk += min(0.5, len(honeypot_flags) * 0.15)

    signals = candidate.get("redrob_signals", {})

    # Ghost candidate
    from core.behavioral import get_days_inactive
    days_inactive = get_days_inactive(signals)
    if days_inactive > 180:
        risk += 0.20
    elif days_inactive > 90:
        risk += 0.10

    # Low response rate
    rr = signals.get("recruiter_response_rate", 0.5)
    if rr < 0.15:
        risk += 0.15
    elif rr < 0.30:
        risk += 0.07

    # Very high notice period
    notice = signals.get("notice_period_days", 60)
    if notice > 120:
        risk += 0.10
    elif notice > 90:
        risk += 0.05

    # Low trust
    if components.get("trust_score", 0.5) < 0.30:
        risk += 0.10

    # Consulting-only career
    career = candidate.get("career_history", [])
    from core.jd_config import JD_CONFIG
    consulting_ratio = sum(
        1 for job in career
        if any(firm in job.get("company", "").lower() for firm in JD_CONFIG["consulting_firms"])
    ) / max(1, len(career))
    risk += consulting_ratio * 0.15

    return round(min(1.0, risk), 2)
