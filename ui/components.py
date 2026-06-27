"""
APTIVA AI — Reusable UI Components
Pre-built blocks for Hireability Index, score bars, skill tags, etc.
"""

import streamlit as st
from ui.icons import icon, icon_text


# -- Recommendation Badge ------------------------------------------------------

def recommendation_badge(label: str) -> str:
    """Return HTML badge for hire recommendation."""
    class_map = {
        "STRONG_YES": "badge-strong-yes",
        "YES":        "badge-yes",
        "MAYBE":      "badge-maybe",
        "NO":         "badge-no",
    }
    text_map = {
        "STRONG_YES": icon_text("badge-check", "Strong Hire"),
        "YES":        icon_text("check-circle", "Hire"),
        "MAYBE":      icon_text("minus", "Maybe"),
        "NO":         icon_text("x-circle", "Pass"),
    }
    cls = class_map.get(label, "badge-neutral")
    txt = text_map.get(label, label)
    return f'<span class="score-badge {cls}">{txt}</span>'


def render_recommendation_badge(label: str):
    st.markdown(recommendation_badge(label), unsafe_allow_html=True)


# -- Hireability Index Display ------------------------------------------------

def render_hireability_index(hi: dict, compact: bool = False):
    """Render the full Hireability Index breakdown."""
    if not hi:
        return

    overall = hi.get("overall", 0)

    # Color based on score
    if overall >= 80:
        color = "#1A8917"
    elif overall >= 65:
        color = "#0071E3"
    elif overall >= 50:
        color = "#C47000"
    else:
        color = "#CC0000"

    if compact:
        st.markdown(
            f"""
<div style="display:flex;align-items:center;gap:0.5rem">
  <span style="font-size:1.75rem;font-weight:800;color:{color};letter-spacing:-0.03em">{overall:.0f}</span>
  <div>
    <div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.08em">Hireability</div>
    <div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.08em">Index</div>
  </div>
</div>""",
            unsafe_allow_html=True,
        )
        return

    # Full display
    st.markdown(
        f"""
<div style="text-align:center;padding:1.5rem;background:#F5F5F7;border-radius:14px;margin-bottom:1rem">
  <div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Hireability Index</div>
  <div style="font-size:4rem;font-weight:800;letter-spacing:-0.04em;color:{color};line-height:1">{overall:.0f}</div>
  <div style="font-size:0.875rem;color:#6E6E73;margin-top:0.25rem">out of 100</div>
</div>""",
        unsafe_allow_html=True,
    )

    # Sub-scores as horizontal bars
    dimensions = [
        ("Technical Fit",     hi.get("technical_fit", 0),    35),
        ("Career Relevance",  hi.get("career_relevance", 0), 25),
        ("Behavior Signals",  hi.get("behavior_signals", 0), 20),
        ("Availability",      hi.get("availability", 0),     10),
        ("Trust Score",       hi.get("trust_score", 0),      10),
    ]

    for label, score, weight in dimensions:
        _render_score_bar(label, score, weight_pct=weight)


def _render_score_bar(label: str, score: float, weight_pct: int = None):
    """Render a single horizontal score bar."""
    fill_color = "#0071E3" if score >= 70 else ("#C47000" if score >= 50 else "#CC0000")
    weight_str = f" <span style='color:#86868B;font-size:0.75rem'>({weight_pct}%)</span>" if weight_pct else ""
    st.markdown(
        f"""
<div style="margin:0.625rem 0">
  <div style="display:flex;justify-content:space-between;font-size:0.8125rem;color:#6E6E73;margin-bottom:0.3rem">
    <span>{label}{weight_str}</span>
    <span style="font-weight:600;color:#1D1D1F">{score:.0f}</span>
  </div>
  <div style="height:5px;background:#E8E8ED;border-radius:5px;overflow:hidden">
    <div style="height:100%;width:{score}%;background:{fill_color};border-radius:5px;transition:width 0.4s ease"></div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )


# -- Score Breakdown Bars ------------------------------------------------------

def render_score_breakdown(components: dict):
    """Render the 7-component score breakdown."""
    items = [
        ("Title Match",        components.get("title", 0),      0.30, "30%"),
        ("Skill Trust",        components.get("skills", 0),     0.25, "25%"),
        ("Career Substance",   components.get("career", 0),     0.20, "20%"),
        ("Experience Fit",     components.get("experience", 0), 0.10, "10%"),
        ("Education",          components.get("education", 0),  0.05, "5%"),
        ("Location",           components.get("location", 0),   0.05, "5%"),
        ("Engagement",         components.get("engagement", 0), 0.05, "5%"),
    ]

    for label, score_01, weight, weight_str in items:
        score_100 = score_01 * 100
        contrib = score_01 * weight * 100
        fill_color = "#0071E3" if score_100 >= 70 else ("#C47000" if score_100 >= 45 else "#CC0000")
        st.markdown(
            f"""
<div style="margin:0.75rem 0">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem">
    <span style="font-size:0.875rem;color:#1D1D1F;font-weight:500">{label}</span>
    <div style="display:flex;align-items:center;gap:0.75rem">
      <span style="font-size:0.75rem;color:#86868B">{weight_str} weight -> +{contrib:.1f}pts</span>
      <span style="font-size:0.9rem;font-weight:700;color:{fill_color}">{score_100:.0f}</span>
    </div>
  </div>
  <div style="height:5px;background:#E8E8ED;border-radius:5px;overflow:hidden">
    <div style="height:100%;width:{score_100}%;background:{fill_color};border-radius:5px"></div>
  </div>
</div>""",
            unsafe_allow_html=True,
        )

    # Behavioral multiplier
    bm = components.get("behavioral_multiplier", 1.0)
    bm_color = "#1A8917" if bm >= 1.0 else ("#C47000" if bm >= 0.75 else "#CC0000")
    _zap = icon("zap", size=14)
    _target = icon("target", size=14)
    st.markdown(
        f"""
<div style="background:#F5F5F7;border-radius:8px;padding:0.75rem 1rem;margin-top:0.5rem;display:flex;justify-content:space-between;align-items:center">
  <span style="font-size:0.875rem;font-weight:500;color:#1D1D1F;display:inline-flex;align-items:center;gap:0.375rem">{_zap} Behavioral Multiplier</span>
  <span style="font-size:1.125rem;font-weight:700;color:{bm_color}">x{bm:.2f}</span>
</div>
<div style="background:#F5F5F7;border-radius:8px;padding:0.75rem 1rem;margin-top:0.375rem;display:flex;justify-content:space-between;align-items:center">
  <span style="font-size:0.875rem;font-weight:600;color:#1D1D1F">Final Score</span>
  <span style="font-size:1.25rem;font-weight:800;color:#0071E3">{components.get('final_score', 0):.4f}</span>
</div>""",
        unsafe_allow_html=True,
    )


# -- Profile Header Card -------------------------------------------------------

def render_profile_header(candidate: dict, components: dict, rank: int = None):
    """Render a clean profile summary card."""
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    hi = components.get("hireability_index", {})

    title = profile.get("current_title", "Unknown Title")
    company = profile.get("current_company", "")
    location = profile.get("location", "")
    yoe = profile.get("years_of_experience", 0)
    notice = signals.get("notice_period_days", 0)
    otw = signals.get("open_to_work_flag", False)
    recommendation = components.get("recommendation", "MAYBE")
    hi_score = hi.get("overall", 0) if hi else 0
    cid = candidate.get("candidate_id", "")

    rank_str = f"<span style='background:#E8F2FF;color:#0071E3;font-size:0.75rem;font-weight:600;padding:0.2rem 0.6rem;border-radius:20px'>Rank #{rank}</span>" if rank else ""
    otw_badge = "<span style='background:#EBF5EA;color:#1A8917;font-size:0.75rem;padding:0.2rem 0.5rem;border-radius:4px;font-weight:500'>Open to Work</span>" if otw else ""

    st.markdown(
        f"""
<div class="aptiva-card" style="display:flex;justify-content:space-between;align-items:flex-start">
  <div>
    <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
      {rank_str}{recommendation_badge(recommendation)}{otw_badge}
    </div>
    <div style="font-size:1.375rem;font-weight:700;color:#1D1D1F;letter-spacing:-0.02em;margin-bottom:0.125rem">{title}</div>
    <div style="font-size:0.9375rem;color:#6E6E73;margin-bottom:0.625rem">{company}{"&nbsp;&nbsp;·&nbsp;&nbsp;" + location if location else ""}</div>
    <div style="display:flex;gap:1.25rem;font-size:0.875rem;color:#86868B">
      <span style="display:inline-flex;align-items:center;gap:0.3rem">{icon("briefcase",14)} {yoe} yrs exp</span>
      <span style="display:inline-flex;align-items:center;gap:0.3rem">{icon("calendar",14)} {notice}d notice</span>
      <span style="font-size:0.75rem;color:#86868B;font-family:monospace">{cid}</span>
    </div>
  </div>
  <div style="text-align:center;min-width:80px">
    <div style="font-size:2.5rem;font-weight:800;color:{'#1A8917' if hi_score>=80 else '#0071E3' if hi_score>=65 else '#C47000' if hi_score>=50 else '#CC0000'};letter-spacing:-0.04em;line-height:1">{hi_score:.0f}</div>
    <div style="font-size:0.625rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.08em">Hireability<br>Index</div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )


# -- AI Insights Panel ---------------------------------------------------------

def render_ai_insights(insights: dict):
    """Render the AI Insights panel with strengths, concerns, etc."""
    if not insights:
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="section-header">Top Strengths</div>', unsafe_allow_html=True)
        for item in insights.get("strengths", []):
            st.markdown(
                f'<div class="insight-item"><span style="color:#1A8917">{icon("check",13)}</span><span>{item}</span></div>',
                unsafe_allow_html=True,
            )
        if not insights.get("strengths"):
            st.markdown('<div style="color:#86868B;font-size:0.875rem">No significant strengths identified</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="section-header">Potential Concerns</div>', unsafe_allow_html=True)
        for item in insights.get("concerns", []):
            st.markdown(
                f'<div class="insight-item"><span style="color:#CC0000">!</span><span>{item}</span></div>',
                unsafe_allow_html=True,
            )
        if not insights.get("concerns"):
            st.markdown('<div style="color:#86868B;font-size:0.875rem">No major concerns</div>', unsafe_allow_html=True)

    st.markdown("---")

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="section-header">Behavior Insights</div>', unsafe_allow_html=True)
        for item in insights.get("behavior_insights", []):
            st.markdown(
                f'<div class="insight-item"><span style="color:#0071E3">{icon("activity",13)}</span><span>{item}</span></div>',
                unsafe_allow_html=True,
            )

    with col4:
        st.markdown('<div class="section-header">Career Trajectory</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.875rem;color:#1D1D1F;padding:0.5rem 0">{insights.get("career_trajectory","—")}</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-header" style="margin-top:0.75rem">Hiring Readiness</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:0.875rem;color:#1D1D1F;padding:0.5rem 0">{insights.get("hiring_readiness","—")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown('<div class="section-header">Market Demand</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-size:0.875rem;color:#6E6E73">{insights.get("market_demand","—")}</div>',
        unsafe_allow_html=True,
    )


# -- Honeypot Warning ----------------------------------------------------------

def render_honeypot_warning(flags: list):
    if not flags:
        return
    st.warning(f"Profile integrity flags detected ({len(flags)} flags): " + " · ".join(flags[:3]))


# -- Empty State ---------------------------------------------------------------

def render_empty_state(message: str = "No data available", hint: str = ""):
    st.markdown(
        f"""
<div style="text-align:center;padding:3rem;color:#86868B">
  <div style="font-size:2rem;margin-bottom:0.5rem">◌</div>
  <div style="font-size:1rem;font-weight:500;color:#6E6E73">{message}</div>
  {"<div style='font-size:0.875rem;margin-top:0.25rem'>" + hint + "</div>" if hint else ""}
</div>""",
        unsafe_allow_html=True,
    )
