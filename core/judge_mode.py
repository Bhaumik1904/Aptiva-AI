"""
APTIVA AI — Judge Mode
Simulates how a recruiter or hackathon judge evaluates a candidate.
Generates structured verdicts for the Judge Mode UI feature.
"""

from typing import Dict

from core.behavioral import get_days_inactive
from core.hireability import get_hire_recommendation
from core.jd_config import JD_CONFIG
from core.skill_gap import get_top_matching_skills, analyze_skill_gap


def generate_judge_verdict(candidate: Dict, components: Dict, rank: int) -> Dict:
    """
    Simulate a senior recruiter's evaluation of a candidate.

    Returns:
        {
            why_recommended: str
            why_not_ranked_higher: str
            biggest_strength: str
            biggest_weakness: str
            risk_factors: list[str]
            interview_recommendation: "YES" | "NO" | "MAYBE"
            final_verdict: str
            verdict_label: "Strong Hire" | "Hire" | "Maybe" | "Pass"
            judge_confidence: float 0-1
        }
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    education = candidate.get("education", [])

    title = profile.get("current_title", "Unknown Title")
    yoe = profile.get("years_of_experience", 0)
    location = profile.get("location", "India")
    company = profile.get("current_company", "")
    notice = signals.get("notice_period_days", 90)
    days_inactive = get_days_inactive(signals)
    hi = components.get("hireability_index", {})
    hi_score = hi.get("overall", 50) if hi else 50

    top_skills = get_top_matching_skills(candidate, 3)
    skill_gap = analyze_skill_gap(candidate)
    missing_core = skill_gap.get("missing_core_skills", [])[:3]
    present_core = skill_gap.get("present_core_skills", [])[:3]

    # ── Why Recommended ───────────────────────────────────────────────────
    why_recommended_parts = []
    if components.get("title", 0) >= 0.75:
        why_recommended_parts.append(f"holds a relevant {title} role")
    if top_skills:
        why_recommended_parts.append(f"has verified expertise in {', '.join(top_skills)}")
    if 5 <= yoe <= 9:
        why_recommended_parts.append(f"{yoe} years of experience squarely in the JD target range")
    if components.get("career", 0) >= 0.65:
        why_recommended_parts.append("career history shows production ML/AI system experience")
    if components.get("availability", 0) >= 0.7:
        why_recommended_parts.append("actively engaged and available")

    if why_recommended_parts:
        why_recommended = f"Candidate {' and '.join(why_recommended_parts[:2])}."
    elif components.get("relevance_gated", False):
        # Issue #4: gated candidates must not receive AI-relevance framing
        why_recommended = (
            f"Candidate's domain relevance (title, skills, career) is below the "
            f"AI/ML scoring threshold for this role. "
            f"Included in the shortlist for completeness only; not recommended for interview."
        )
    else:
        why_recommended = (
            f"Partial match with JD — some transferable signals present. "
            f"Final Score {components.get('final_score', 0):.4f} reflects limited direct alignment "
            f"with the Senior AI Engineer requirements."
        )

    # ── Why Not Ranked Higher ─────────────────────────────────────────────
    why_not_higher_parts = []

    if missing_core:
        why_not_higher_parts.append(f"missing key JD requirements: {', '.join(missing_core[:2])}")
    if days_inactive > 60:
        why_not_higher_parts.append(f"platform inactivity ({days_inactive} days) signals lower urgency")
    if notice > 90:
        why_not_higher_parts.append(f"long notice period ({notice} days) reduces immediacy")
    if components.get("title", 0) < 0.70:
        why_not_higher_parts.append("title not a direct AI Engineer match")
    is_consulting = any(firm in company.lower() for firm in JD_CONFIG["consulting_firms"])
    if is_consulting:
        why_not_higher_parts.append(f"consulting background ({company}) per JD preference")
    if components.get("career", 0) < 0.50:
        why_not_higher_parts.append("career descriptions lack depth in retrieval/ranking systems")

    if why_not_higher_parts:
        why_not_higher = f"Ranked #{rank} due to: {'; '.join(why_not_higher_parts[:2])}."
    else:
        why_not_higher = f"Candidate is well-ranked; minor gaps prevent a higher position."

    # ── Biggest Strength ──────────────────────────────────────────────────
    strength_candidates = []
    if top_skills:
        strength_candidates.append(
            (components.get("skills", 0), f"Strong expertise in {', '.join(top_skills[:2])} — directly relevant to the JD")
        )
    if components.get("career", 0) >= 0.65:
        strength_candidates.append(
            (components.get("career", 0), "Production ML system experience in career history")
        )
    if components.get("title", 0) >= 0.85:
        strength_candidates.append(
            (components.get("title", 0), f"Title ({title}) is a strong match for the Senior AI Engineer role")
        )
    if hi.get("trust_score", 0) >= 75:
        strength_candidates.append(
            (hi.get("trust_score", 0) / 100, "Highly verified profile with strong platform trust signals")
        )
    if 6 <= yoe <= 8:
        strength_candidates.append(
            (0.9, f"Optimal experience level ({yoe} years) — exactly what the JD targets")
        )

    if strength_candidates:
        strength_candidates.sort(key=lambda x: x[0], reverse=True)
        biggest_strength = strength_candidates[0][1]
    else:
        biggest_strength = "Adjacent technical background with transferable skills."

    # ── Biggest Weakness ──────────────────────────────────────────────────
    weakness_candidates = []
    if missing_core:
        weakness_candidates.append(
            (len(missing_core), f"Missing core JD skills: {', '.join(missing_core[:3])}")
        )
    if notice > 90:
        weakness_candidates.append((notice / 180, f"{notice}-day notice period"))
    if days_inactive > 90:
        weakness_candidates.append((days_inactive / 365, f"{days_inactive} days inactive on platform"))
    if is_consulting:
        weakness_candidates.append((0.6, f"Consulting-firm background ({company}) — JD explicitly disfavors this"))
    if yoe < 4:
        weakness_candidates.append((0.8, f"Only {yoe} years of experience; JD targets 5–9"))
    if components.get("title", 0) < 0.40:
        weakness_candidates.append((0.9, f"Title '{title}' is not aligned with AI Engineering"))

    if weakness_candidates:
        weakness_candidates.sort(key=lambda x: x[0], reverse=True)
        biggest_weakness = weakness_candidates[0][1]
    else:
        biggest_weakness = "No critical weaknesses identified — minor gaps only."

    # ── Risk Factors ──────────────────────────────────────────────────────
    risk_factors = []
    risk_score = components.get("risk_score", 0)

    if components.get("honeypot", False):
        risk_factors.append("⚠️ Profile integrity flags detected")
    if days_inactive > 180:
        risk_factors.append(f"Ghost candidate risk — {days_inactive} days since last activity")
    if signals.get("recruiter_response_rate", 0.5) < 0.15:
        risk_factors.append("Very low recruiter response rate — may not convert")
    if notice > 120:
        risk_factors.append(f"Extreme notice period ({notice} days) — delays onboarding")
    if is_consulting:
        risk_factors.append("Consulting background — may lack product company mindset")
    if risk_score > 0.4:
        risk_factors.append(f"Elevated composite risk score: {risk_score:.0%}")

    if not risk_factors:
        risk_factors.append("No significant risk factors identified")

    # ── Interview Recommendation ──────────────────────────────────────────
    # Issue #3: Final Score is the primary cited metric in all verdict text.
    # HI appears only as a secondary supporting metric where relevant.
    recommendation = components.get("recommendation", "MAYBE")
    final_score_val = components.get("final_score", 0)
    if recommendation == "STRONG_YES":
        interview_rec = "YES"
        verdict_label = "Strong Hire"
        final_verdict = (
            f"Strongly recommend for interview. Final Score {final_score_val:.4f} — "
            f"{title} with {yoe} years of experience and strong signal alignment with the JD. "
            f"Hireability Index {hi_score:.0f}/100 confirms readiness. "
            f"Priority candidate — schedule immediately."
        )
    elif recommendation == "YES":
        interview_rec = "YES"
        verdict_label = "Hire"
        final_verdict = (
            f"Recommend for interview. Final Score {final_score_val:.4f} — "
            f"solid fit across key dimensions for the Senior AI Engineer role. "
            f"Worth pursuing — confirm skills in technical screen."
        )
    elif recommendation == "MAYBE":
        interview_rec = "MAYBE"
        verdict_label = "Maybe"
        final_verdict = (
            f"Borderline candidate. Final Score {final_score_val:.4f} — "
            f"some JD alignment present but gaps exist (Hireability Index {hi_score:.0f}/100). "
            f"Consider for a screening call if pipeline is thin."
        )
    else:
        interview_rec = "NO"
        verdict_label = "Pass"
        if components.get("relevance_gated", False):
            # Issue #4: gated candidates get an explicit domain-gate explanation
            final_verdict = (
                f"Do not recommend. Final Score {final_score_val:.4f} — "
                f"candidate's domain relevance (title + skills + career) is below the "
                f"AI/ML threshold for this role. Not suitable for the Senior AI Engineer position."
            )
        else:
            final_verdict = (
                f"Do not recommend at this time. Final Score {final_score_val:.4f} — "
                f"significant gaps relative to the Senior AI Engineer JD requirements. "
                f"Consider only if requirements change."
            )

    # Judge confidence
    confidence = components.get("confidence_score", 0.5)

    return {
        "why_recommended":        why_recommended,
        "why_not_ranked_higher":  why_not_higher,
        "biggest_strength":       biggest_strength,
        "biggest_weakness":       biggest_weakness,
        "risk_factors":           risk_factors,
        "interview_recommendation": interview_rec,
        "final_verdict":          final_verdict,
        "verdict_label":          verdict_label,
        "judge_confidence":       confidence,
    }
