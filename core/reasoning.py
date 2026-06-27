"""
APTIVA AI — Reasoning Generator
Template-based reasoning. Specific, honest, non-hallucinated.
Optionally loads enriched reasoning from precomputed_reasonings.json.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.behavioral import get_days_inactive
from core.jd_config import JD_CONFIG
from core.skill_gap import get_top_matching_skills

PRECOMPUTED_PATH = Path("precomputed_reasonings.json")


def load_precomputed_reasonings() -> Dict[str, str]:
    """Load enriched reasonings if available."""
    if PRECOMPUTED_PATH.exists():
        try:
            with open(PRECOMPUTED_PATH, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


_precomputed: Optional[Dict[str, str]] = None


def get_precomputed() -> Dict[str, str]:
    global _precomputed
    if _precomputed is None:
        _precomputed = load_precomputed_reasonings()
    return _precomputed


def generate_reasoning(
    candidate: Dict,
    rank: int,
    components: Dict,
    use_precomputed: bool = True,
) -> str:
    """
    Generate a 1–2 sentence reasoning string for a candidate.
    If precomputed enriched reasoning exists, use that instead.
    """
    cid = candidate.get("candidate_id", "")

    # Use enriched reasoning if available
    if use_precomputed:
        precomputed = get_precomputed()
        if cid in precomputed:
            return precomputed[cid]

    return _template_reasoning(candidate, rank, components)


def _template_reasoning(candidate: Dict, rank: int, components: Dict) -> str:
    """Build a specific, fact-grounded reasoning string from templates.

    Implements:
      Issue #3 — Relevance-gated candidates receive gate-disclosure reasoning only.
      Issue #1 — Top-10 ranks cite Final Score as primary metric; HI is secondary.
      Issue #2 — All rank branches cite Final Score so every CSV row is self-auditable.
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    title = profile.get("current_title", "Unknown Title")
    yoe = profile.get("years_of_experience", 0)
    location = profile.get("location", "India")
    current_company = profile.get("current_company", "")
    notice = signals.get("notice_period_days", 90)
    response_rate = signals.get("recruiter_response_rate", 0.5)
    days_inactive = get_days_inactive(signals)
    hi = components.get("hireability_index", {})
    hi_score = hi.get("overall", 50) if hi else 50
    final_score = components.get("final_score", 0)

    # -- Issue #3: Relevance Gate disclosure ----------------------------------
    # Short-circuit before any template branch — gated candidates must not
    # receive reasoning that implies JD domain fit.
    if components.get("relevance_gated", False):
        return (
            f"Relevance Gate applied: domain relevance below AI/ML threshold "
            f"(title + skills + career signal < 0.01); '{title}' is outside the "
            f"target AI/ML engineering domain. "
            f"Final Score {final_score:.4f} capped by gate. "
            f"Included in top-100 for completeness; not a recommended JD fit."
        )

    # Top matching skills
    matching_skills = get_top_matching_skills(candidate, n=3)
    skill_str = ", ".join(matching_skills) if matching_skills else "AI-adjacent skills"

    strengths = []
    concerns = []

    # Title strength
    title_score = components.get("title", 0)
    if title_score >= 0.85:
        strengths.append(f"{title} directly aligns with JD requirements")
    elif title_score >= 0.55:
        strengths.append(f"{title} is adjacent to the target AI Engineer role")
    else:
        concerns.append(f"title ({title}) is not a core AI/ML role")

    # Skills
    if matching_skills:
        strengths.append(f"demonstrated {skill_str} expertise")

    # Experience
    if 5 <= yoe <= 9:
        strengths.append(f"{yoe}yr experience within JD target range")
    elif yoe > 9:
        concerns.append(f"{yoe}yr experience slightly above JD target (5–9yr)")
    else:
        concerns.append(f"only {yoe}yr experience (JD targets 5–9yr)")

    # Company context
    if current_company:
        is_consulting = any(firm in current_company.lower() for firm in JD_CONFIG["consulting_firms"])
        if is_consulting:
            concerns.append(f"currently at consulting firm ({current_company})")
        elif components.get("career", 0) >= 0.65:
            strengths.append(f"strong production ML background at {current_company}")

    # Availability
    if notice <= 30:
        strengths.append(f"{notice}d notice (immediately buyable)")
    elif notice > 90:
        concerns.append(f"{notice}d notice period")

    if days_inactive > 180:
        concerns.append(f"last active {days_inactive}d ago (availability risk)")
    elif days_inactive <= 14:
        strengths.append("actively engaged on platform")

    if response_rate < 0.20:
        concerns.append(f"low recruiter response rate ({response_rate:.0%})")

    # Assemble shared parts
    s_str = "; ".join(strengths[:2]) if strengths else "adequate profile fit"
    c_str = (f"; concern: {concerns[0]}" if concerns else "")

    # -- Issue #1: Top-10 — Final Score is the primary cited metric -----------
    if rank <= 10:
        return (
            f"Rank #{rank}: {s_str}, {location}-based, "
            f"Final Score {final_score:.4f} (HI {hi_score:.0f}/100){c_str}."
        )
    # -- Issue #2: Ranks 11–50 — append Final Score so every row is auditable -
    elif rank <= 50:
        return f"{s_str}, {location} [FS {final_score:.4f}]{c_str}."
    # -- Issue #2: Ranks 51–100 — explicit Final Score replaces vague text ----
    else:
        first = strengths[0] if strengths else "adjacent candidate"
        concern_part = f"; concern: {concerns[0]}" if concerns else ""
        return (
            f"{first}{concern_part}; "
            f"Final Score {final_score:.4f} reflects weaker JD signal alignment."
        )


def generate_ai_insights(candidate: Dict, components: Dict) -> Dict:
    """
    Generate structured AI Insights for the UI panels.
    Returns dict with: strengths, concerns, behavior_insights,
                       career_trajectory, hiring_readiness, market_demand
    """
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])

    title = profile.get("current_title", "")
    yoe = profile.get("years_of_experience", 0)
    hi = components.get("hireability_index", {})
    hi_score = hi.get("overall", 50) if hi else 50
    days_inactive = get_days_inactive(signals)

    # Strengths
    strengths = []
    if components.get("title", 0) >= 0.75:
        strengths.append(f"Strong title alignment: {title}")
    if components.get("skills", 0) >= 0.60:
        matching = get_top_matching_skills(candidate, 3)
        if matching:
            strengths.append(f"Verified core skills: {', '.join(matching)}")
    if 6 <= yoe <= 8:
        strengths.append(f"Optimal experience level ({yoe} years)")
    if components.get("career", 0) >= 0.65:
        strengths.append("Production ML experience in career history")
    if signals.get("github_activity_score", -1) >= 40:
        strengths.append(f"Active GitHub presence (score: {signals['github_activity_score']})")
    if components.get("trust_score", 0) >= 0.75:
        strengths.append("High trust score — verified contact & assessments")

    # Concerns
    concerns = []
    if components.get("title", 0) < 0.50:
        concerns.append(f"Title mismatch: '{title}' is not a core AI/ML role")
    if days_inactive > 90:
        concerns.append(f"Not active for {days_inactive} days")
    notice = signals.get("notice_period_days", 60)
    if notice > 90:
        concerns.append(f"{notice}-day notice period limits immediate availability")
    if components.get("skills", 0) < 0.30:
        concerns.append("Limited verified AI/ML skills")
    consulting_match = any(
        firm in profile.get("current_company", "").lower()
        for firm in JD_CONFIG["consulting_firms"]
    )
    if consulting_match:
        concerns.append("Current employer is a consulting firm (JD disfavors this)")
    if components.get("risk_score", 0) > 0.5:
        concerns.append("Elevated risk indicators detected")

    # Behavior insights
    behavior_insights = []
    rr = signals.get("recruiter_response_rate", 0.5)
    if rr >= 0.6:
        behavior_insights.append(f"Responsive to recruiters ({rr:.0%} response rate)")
    elif rr < 0.2:
        behavior_insights.append(f"Low recruiter response rate ({rr:.0%}) — may not be actively looking")
    if signals.get("open_to_work_flag", False):
        behavior_insights.append("Explicitly open to work")
    apps = signals.get("applications_submitted_30d", 0)
    if apps >= 5:
        behavior_insights.append(f"Active job seeker ({apps} applications in 30 days)")
    saved = signals.get("saved_by_recruiters_30d", 0)
    if saved >= 5:
        behavior_insights.append(f"In demand — saved by {saved} recruiters recently")

    # Career trajectory
    titles = [job.get("title", "") for job in career]
    trajectory = "Steady progression" if len(set(titles)) > 2 else "Limited role variety"
    if any("senior" in t.lower() or "lead" in t.lower() or "principal" in t.lower() for t in titles):
        trajectory = "Upward trajectory with leadership roles"

    # Hiring readiness — Issue #6: driven by recommendation (Final Score gate),
    # not HI score, to ensure consistency with the recommendation badge on the
    # same page. Eliminates the contradiction where recommendation=NO could
    # coexist with "interview recommended" hiring_readiness text.
    recommendation_val = components.get("recommendation", "NO")
    if recommendation_val == "STRONG_YES":
        hiring_readiness = "Ready to hire — strong across all scoring dimensions"
    elif recommendation_val == "YES":
        hiring_readiness = "Good candidate — recommend for technical screen"
    elif recommendation_val == "MAYBE":
        hiring_readiness = "Borderline — screening call warranted if pipeline is thin"
    else:
        hiring_readiness = "Not recommended — below scoring threshold for this role"

    # Market demand
    profile_views = signals.get("profile_views_received_30d", 0)
    if profile_views >= 20:
        market_demand = f"High market demand — {profile_views} profile views in 30 days"
    elif profile_views >= 5:
        market_demand = f"Moderate market interest — {profile_views} profile views in 30 days"
    else:
        market_demand = "Limited recent market activity"

    return {
        "strengths": strengths[:5],
        "concerns": concerns[:4],
        "behavior_insights": behavior_insights[:4],
        "career_trajectory": trajectory,
        "hiring_readiness": hiring_readiness,
        "market_demand": market_demand,
    }
