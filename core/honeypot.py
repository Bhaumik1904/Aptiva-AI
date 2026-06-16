"""
APTIVA AI — Honeypot Detector
Identifies fraudulent or impossible candidate profiles before scoring.
"""

from datetime import datetime
from typing import Dict, List, Tuple


def detect_honeypot(candidate: Dict) -> Tuple[bool, List[str]]:
    """
    Returns (is_honeypot, list_of_flags).
    Two or more flags = honeypot; candidate score is set to near-zero.
    """
    flags: List[str] = []
    today = datetime.now().date()

    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    signals = candidate.get("redrob_signals", {})

    # ── Career Temporal Checks ─────────────────────────────────────────────
    for job in career:
        try:
            start_str = job.get("start_date", "")
            end_str = job.get("end_date", "")
            if not start_str:
                continue

            start = datetime.strptime(start_str[:10], "%Y-%m-%d").date()
            end = datetime.strptime(end_str[:10], "%Y-%m-%d").date() if end_str else today

            # Future start date
            if start > today:
                flags.append("future_start_date")

            # End before start
            if end < start:
                flags.append("end_before_start")

            # Duration mismatch (stated vs calculated, >6 months off)
            stated_months = job.get("duration_months", 0)
            actual_months = (end.year - start.year) * 12 + (end.month - start.month)
            if stated_months > 0 and abs(actual_months - stated_months) > 8:
                flags.append(f"duration_mismatch:{job.get('company','?')}")

        except (ValueError, TypeError):
            pass  # Unparseable dates are suspicious but not definitive

    # ── Education Temporal Checks ──────────────────────────────────────────
    for edu in education:
        try:
            start_year = int(edu.get("start_year", 0))
            end_year = int(edu.get("end_year", 0))
            if end_year and start_year and end_year < start_year:
                flags.append("education_year_impossible")
            # Still in school but very senior
            current_year = datetime.now().year
            if end_year > current_year + 1 and profile.get("years_of_experience", 0) > 15:
                flags.append("still_studying_but_overly_senior")
        except (ValueError, TypeError):
            pass

    # ── Skill Impossibilities ──────────────────────────────────────────────
    expert_zero_count = 0
    for skill in skills:
        proficiency = skill.get("proficiency", "")
        duration = skill.get("duration_months", 1)
        name = skill.get("name", "?")

        # Expert with zero duration is impossible
        if proficiency == "expert" and duration == 0:
            expert_zero_count += 1
            if expert_zero_count <= 3:  # Flag up to 3
                flags.append(f"expert_zero_duration:{name}")

    # Many experts but short career
    expert_count = sum(1 for s in skills if s.get("proficiency") == "expert")
    yoe = profile.get("years_of_experience", 0)
    if expert_count > 8 and yoe < 4:
        flags.append(f"too_many_experts_for_experience:({expert_count} experts, {yoe}yr)")

    # ── Assessment vs Self-Reported Contradiction ──────────────────────────
    assessments = signals.get("skill_assessment_scores", {})
    for skill in skills:
        name = skill.get("name", "")
        if skill.get("proficiency") == "expert" and name in assessments:
            if assessments[name] < 25:
                flags.append(f"expert_failed_assessment:{name}({assessments[name]})")

    # ── Profile Completeness Ghost ─────────────────────────────────────────
    completeness = signals.get("profile_completeness_score", 50)
    if completeness < 20:
        flags.append(f"ghost_profile:completeness={completeness}")

    # ── Final Decision: 2+ flags = honeypot ───────────────────────────────
    is_honeypot = len(flags) >= 2
    return is_honeypot, flags
