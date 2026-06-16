"""
APTIVA AI — Skill Gap Engine
Analyzes the gap between JD requirements and candidate skills.
Produces required / present / missing / bonus breakdowns.
"""

from typing import Dict, List, Tuple

from core.jd_config import JD_CONFIG


def _normalize(name: str) -> str:
    return name.lower().strip().replace("-", " ").replace("_", " ")


def _skills_match(candidate_skill: str, jd_skill: str) -> bool:
    """Bidirectional fuzzy substring match."""
    c = _normalize(candidate_skill)
    j = _normalize(jd_skill)
    return j in c or c in j


def analyze_skill_gap(candidate: Dict) -> Dict:
    """
    Returns a comprehensive skill gap analysis.

    Returns:
        {
            "required_skills": list of {name, status, candidate_skill, proficiency, duration_months, match_score}
            "present_core_skills": list of matched core skill names
            "missing_core_skills": list of unmatched core skill names
            "bonus_skills": list of matched bonus skill names
            "unmatched_bonus": list of unmatched bonus skill names
            "candidate_unique_skills": list of candidate skills not in JD at all
            "skill_match_pct": float 0-100
            "core_match_pct": float 0-100
            "bonus_match_pct": float 0-100
        }
    """
    candidate_skills = candidate.get("skills", [])
    assessments = candidate.get("redrob_signals", {}).get("skill_assessment_scores", {})

    # Index candidate skills for fast lookup
    c_skill_names = [s.get("name", "") for s in candidate_skills]

    # ── Core Skills Analysis ──────────────────────────────────────────────
    required_skills = []
    present_core = []
    missing_core = []

    for jd_skill in JD_CONFIG["core_skills"]:
        matched = None
        for cs in candidate_skills:
            if _skills_match(cs.get("name", ""), jd_skill):
                matched = cs
                break

        if matched:
            name = matched.get("name", jd_skill)
            proficiency = matched.get("proficiency", "unknown")
            duration = matched.get("duration_months", 0)
            endorsements = matched.get("endorsements", 0)

            # Assessment override if available
            assessment_val = None
            for akey in assessments:
                if _skills_match(akey, jd_skill):
                    assessment_val = assessments[akey]
                    break

            required_skills.append({
                "name": jd_skill,
                "status": "present",
                "candidate_skill": name,
                "proficiency": proficiency,
                "duration_months": duration,
                "endorsements": endorsements,
                "assessment_score": assessment_val,
                "match_quality": _compute_match_quality(matched, assessment_val),
            })
            present_core.append(jd_skill)
        else:
            required_skills.append({
                "name": jd_skill,
                "status": "missing",
                "candidate_skill": None,
                "proficiency": None,
                "duration_months": None,
                "endorsements": None,
                "assessment_score": None,
                "match_quality": 0.0,
            })
            missing_core.append(jd_skill)

    # ── Bonus Skills Analysis ─────────────────────────────────────────────
    present_bonus = []
    missing_bonus = []

    for jd_skill in JD_CONFIG["bonus_skills"]:
        for cs in candidate_skills:
            if _skills_match(cs.get("name", ""), jd_skill):
                present_bonus.append(jd_skill)
                break
        else:
            missing_bonus.append(jd_skill)

    # ── Candidate Unique Skills (not in JD at all) ─────────────────────────
    all_jd_skills = JD_CONFIG["core_skills"] + JD_CONFIG["bonus_skills"]
    unique_skills = []
    for cs in candidate_skills:
        name = cs.get("name", "")
        if not any(_skills_match(name, jd_s) for jd_s in all_jd_skills):
            unique_skills.append({
                "name": name,
                "proficiency": cs.get("proficiency", "unknown"),
                "duration_months": cs.get("duration_months", 0),
            })

    # ── Percentages ───────────────────────────────────────────────────────
    core_match_pct = len(present_core) / max(1, len(JD_CONFIG["core_skills"])) * 100
    bonus_match_pct = len(present_bonus) / max(1, len(JD_CONFIG["bonus_skills"])) * 100
    total_jd = len(JD_CONFIG["core_skills"]) + len(JD_CONFIG["bonus_skills"])
    skill_match_pct = (len(present_core) + len(present_bonus)) / max(1, total_jd) * 100

    return {
        "required_skills": required_skills,
        "present_core_skills": present_core,
        "missing_core_skills": missing_core,
        "bonus_skills_matched": present_bonus,
        "bonus_skills_missing": missing_bonus,
        "candidate_unique_skills": unique_skills[:10],  # Cap at 10
        "skill_match_pct": round(skill_match_pct, 1),
        "core_match_pct": round(core_match_pct, 1),
        "bonus_match_pct": round(bonus_match_pct, 1),
    }


def _compute_match_quality(skill: Dict, assessment_val) -> float:
    """0.0–1.0 quality of a matched skill (proficiency × duration × assessment)."""
    prof_map = {"beginner": 0.25, "intermediate": 0.55, "advanced": 0.80, "expert": 1.0}
    prof = prof_map.get(skill.get("proficiency", "intermediate"), 0.55)

    duration = skill.get("duration_months", 0)
    dur_score = min(1.0, duration / 36)  # Cap at 3 years

    if assessment_val is not None:
        # Blend proficiency with assessment
        prof = 0.4 * prof + 0.6 * (assessment_val / 100)

    endorsements = skill.get("endorsements", 0)
    endorse_score = min(1.0, endorsements / 30)

    return round(0.5 * prof + 0.3 * dur_score + 0.2 * endorse_score, 2)


def get_top_matching_skills(candidate: Dict, n: int = 5) -> List[str]:
    """Return the top-N matching core skills by match quality."""
    gap = analyze_skill_gap(candidate)
    present = [s for s in gap["required_skills"] if s["status"] == "present"]
    present.sort(key=lambda x: x["match_quality"], reverse=True)
    return [s["candidate_skill"] or s["name"] for s in present[:n]]
