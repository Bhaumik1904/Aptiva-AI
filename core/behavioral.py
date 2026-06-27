"""
APTIVA AI — Behavioral Multiplier & Availability/Trust Scores
Computes the behavioral engagement multiplier (0.75–1.15) and
sub-scores for Availability and Trust used in the Hireability Index.

System B (Soft BM): clamp range reduced from [0.10, 1.25] to [0.75, 1.15].
Behavioral signals act as a secondary tiebreaker (+/-15%), not a ranking engine.
All internal signal logic is unchanged.
"""

from datetime import datetime
from typing import Dict, Tuple


def compute_behavioral_multiplier(candidate: Dict) -> float:
    """
    Multiplicative modifier applied to the base score.
    Range: 0.75 (low engagement) to 1.15 (highly engaged).

    System B Soft BM: final score clamped to [0.75, 1.15] after all
    signal calculations, so behavioral signals adjust ranking by at most
    +/-15% rather than acting as a primary ranking determinant.
    """
    signals = candidate.get("redrob_signals", {})
    today = datetime.now().date()

    score = 1.0

    # -- Recency of Activity -----------------------------------------------
    try:
        last_active_str = signals.get("last_active_date", "")
        last_active = datetime.strptime(last_active_str[:10], "%Y-%m-%d").date()
        days_inactive = (today - last_active).days
    except (ValueError, TypeError):
        days_inactive = 365  # Assume old if unparseable

    if days_inactive <= 7:
        score *= 1.15
    elif days_inactive <= 30:
        score *= 1.05
    elif days_inactive <= 90:
        score *= 1.00
    elif days_inactive <= 180:
        score *= 0.75
    else:
        score *= 0.40  # Ghost candidate

    # -- Open to Work -----------------------------------------------------
    if signals.get("open_to_work_flag", False):
        score *= 1.10

    # -- Notice Period -----------------------------------------------------
    notice = signals.get("notice_period_days", 90)
    if notice <= 15:
        score *= 1.12
    elif notice <= 30:
        score *= 1.10
    elif notice <= 60:
        score *= 1.00
    elif notice <= 90:
        score *= 0.90
    elif notice <= 120:
        score *= 0.75
    else:
        score *= 0.60  # 120+ day notice is near-disqualifying

    # -- Recruiter Response Rate -------------------------------------------
    rr = signals.get("recruiter_response_rate", 0.5)
    if rr >= 0.70:
        score *= 1.10
    elif rr >= 0.40:
        score *= 1.00
    elif rr >= 0.20:
        score *= 0.85
    else:
        score *= 0.65  # Won't respond

    # -- Interview Completion Rate -----------------------------------------
    icr = signals.get("interview_completion_rate", 0.6)
    if icr >= 0.80:
        score *= 1.05
    elif icr >= 0.60:
        score *= 1.00
    elif icr < 0.40:
        score *= 0.85

    # -- Average Response Time ---------------------------------------------
    art = signals.get("avg_response_time_hours", 48)
    if art <= 24:
        score *= 1.05
    elif art <= 72:
        score *= 1.00
    elif art > 168:  # > 1 week
        score *= 0.90

    # -- Profile Completeness ----------------------------------------------
    pcs = signals.get("profile_completeness_score", 50)
    if pcs >= 80:
        score *= 1.05
    elif pcs < 40:
        score *= 0.80

    # -- GitHub Activity ---------------------------------------------------
    github = signals.get("github_activity_score", -1)
    if github == -1:
        score *= 0.95  # No GitHub is mild negative for AI Engineer
    elif github >= 60:
        score *= 1.08
    elif github >= 30:
        score *= 1.03

    # -- Verification -----------------------------------------------------
    verified = int(signals.get("verified_email", False)) + int(signals.get("verified_phone", False))
    score *= (0.90 + verified * 0.05)  # 0.90 / 0.95 / 1.00

    # -- Recruiter Market Interest -----------------------------------------
    saved = signals.get("saved_by_recruiters_30d", 0)
    if saved >= 10:
        score *= 1.05
    elif saved >= 3:
        score *= 1.02

    # -- Offer Acceptance Rate ---------------------------------------------
    oar = signals.get("offer_acceptance_rate", -1)
    if oar != -1:
        if oar >= 0.70:
            score *= 1.05
        elif oar < 0.20:
            score *= 0.95

    return max(0.75, min(1.15, score))  # System B: clamp to [0.75, 1.15]


def compute_availability_score(signals: Dict) -> float:
    """
    0.0–1.0 availability sub-score for Hireability Index.
    Focuses on: recency, open-to-work, notice period, applications.
    """
    today = datetime.now().date()
    score = 0.0

    # Last active recency (30% weight)
    try:
        last_active = datetime.strptime(signals.get("last_active_date", "")[:10], "%Y-%m-%d").date()
        days_inactive = (today - last_active).days
        if days_inactive <= 7:
            recency = 1.0
        elif days_inactive <= 30:
            recency = 0.85
        elif days_inactive <= 90:
            recency = 0.65
        elif days_inactive <= 180:
            recency = 0.35
        else:
            recency = 0.10
    except (ValueError, TypeError):
        recency = 0.30
    score += 0.30 * recency

    # Open to work (25% weight)
    score += 0.25 * int(signals.get("open_to_work_flag", False))

    # Notice period (30% weight)
    notice = signals.get("notice_period_days", 90)
    if notice <= 15:
        notice_s = 1.0
    elif notice <= 30:
        notice_s = 0.90
    elif notice <= 60:
        notice_s = 0.70
    elif notice <= 90:
        notice_s = 0.50
    elif notice <= 120:
        notice_s = 0.30
    else:
        notice_s = 0.10
    score += 0.30 * notice_s

    # Applications submitted 30d (15% weight — actively looking)
    apps = min(10, signals.get("applications_submitted_30d", 0))
    score += 0.15 * (apps / 10)

    return min(1.0, score)


def compute_trust_score(candidate: Dict) -> float:
    """
    0.0–1.0 trust sub-score for Hireability Index.
    Focuses on: verifications, completeness, LinkedIn, assessments.
    """
    signals = candidate.get("redrob_signals", {})
    score = 0.0

    # Verified contact info (40% combined)
    score += 0.20 * int(signals.get("verified_email", False))
    score += 0.20 * int(signals.get("verified_phone", False))

    # Profile completeness (20%)
    score += 0.20 * (signals.get("profile_completeness_score", 0) / 100)

    # LinkedIn connected (10%)
    score += 0.10 * int(signals.get("linkedin_connected", False))

    # Skill assessment scores (30%) — platform-verified
    assessment_scores = signals.get("skill_assessment_scores", {})
    if assessment_scores:
        avg_assessment = sum(assessment_scores.values()) / len(assessment_scores) / 100
        score += 0.30 * avg_assessment
    else:
        score += 0.15  # Neutral when no assessments taken

    return min(1.0, score)


def get_days_inactive(signals: Dict) -> int:
    """Helper: days since last active."""
    try:
        last_active = datetime.strptime(
            signals.get("last_active_date", "")[:10], "%Y-%m-%d"
        ).date()
        return (datetime.now().date() - last_active).days
    except (ValueError, TypeError):
        return 999
