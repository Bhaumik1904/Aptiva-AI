"""
APTIVA AI — AI Analysis Page
The most polished and impressive screen. Shows every analytical dimension
of a candidate in a single unified view.
"""

import streamlit as st

from core.reasoning import generate_ai_insights
from core.skill_gap import analyze_skill_gap
from ui.charts import (
    behavioral_radar,
    hireability_gauge,
    score_breakdown_chart,
    skill_match_chart,
)
from ui.components import (
    render_ai_insights,
    render_hireability_index,
    render_honeypot_warning,
    render_profile_header,
    render_recommendation_badge,
    render_score_breakdown,
)
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the AI Analysis page — the most important screen."""
    page_header(
        "AI Analysis",
        "Deep intelligence on every candidate dimension · Powered by APTIVA AI",
        "🤖",
    )

    # ── Candidate Selection ───────────────────────────────────────────────
    results = state.get("results", [])
    if not results:
        st.info("No candidates loaded. Run the ranker first.")
        return

    candidate_options = {
        f"#{r['rank']} · {r['candidate']['candidate_id']} · {r['candidate']['profile'].get('current_title', '')[:30]}": r["candidate"]["candidate_id"]
        for r in results
    }

    _, col_sel = st.columns([2, 1])
    with col_sel:
        new_selection = st.selectbox(
            "Select Candidate to Analyse",
            list(candidate_options.keys()),
            index=next((i for i, v in enumerate(candidate_options.values()) if v == state.get("selected_candidate_id")), 0),
            key="ai_analysis_select",
        )
        if new_selection:
            new_cid = candidate_options[new_selection]
            if new_cid != state.get("selected_candidate_id"):
                st.session_state["selected_candidate_id"] = new_cid
                st.rerun()

    result = _get_selected_result(state)
    if not result:
        st.info("Select a candidate from the Rankings page to view AI Analysis.")
        return

    candidate = result["candidate"]
    components = result.get("components", {})
    rank = result["rank"]
    score = result["score"]

    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    hi = components.get("hireability_index", {})
    hi_score = hi.get("overall", 0) if hi else 0
    recommendation = components.get("recommendation", "MAYBE")
    confidence = components.get("confidence_score", 0)
    risk_score = components.get("risk_score", 0)
    honeypot_flags = components.get("honeypot_flags", [])

    # ── Profile Header ────────────────────────────────────────────────────
    render_profile_header(candidate, components, rank)

    if honeypot_flags:
        render_honeypot_warning(honeypot_flags)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── TOP ROW: 6 Key Metrics ────────────────────────────────────────────
    section_label("KEY METRICS")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.metric("Overall Score", f"{score:.4f}")
    with m2:
        st.metric("Hireability Index™", f"{hi_score:.0f}/100")
    with m3:
        st.metric("Rank", f"#{rank}")
    with m4:
        st.metric("Confidence", f"{confidence:.0%}")
    with m5:
        risk_delta = "🟢 Low" if risk_score < 0.25 else "🟡 Medium" if risk_score < 0.5 else "🔴 High"
        st.metric("Risk", risk_delta)
    with m6:
        skill_gap = analyze_skill_gap(candidate)
        st.metric("Skill Match", f"{skill_gap.get('core_match_pct', 0):.0f}%")

    st.markdown("---")

    # ── MIDDLE ROW: Gauge + Hireability Breakdown + Behavior ─────────────
    col_left, col_mid, col_right = st.columns([1.2, 1.8, 2])

    with col_left:
        section_label("HIREABILITY INDEX™")
        hi_fig = hireability_gauge(hi_score)
        st.plotly_chart(hi_fig, use_container_width=True, config={"displayModeBar": False})

        # Recommendation badge
        render_recommendation_badge(recommendation)
        st.markdown(
            f'<div style="font-size:0.8125rem;color:#6E6E73;margin-top:0.5rem">Confidence: <strong>{confidence:.0%}</strong></div>',
            unsafe_allow_html=True,
        )

    with col_mid:
        section_label("HIREABILITY BREAKDOWN")
        render_hireability_index(hi, compact=False)

    with col_right:
        section_label("BEHAVIORAL SIGNALS")
        radar_fig = behavioral_radar(signals)
        st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # ── SECOND ROW: Score Breakdown + Skill Gap ───────────────────────────
    col_scores, col_skills = st.columns([1.5, 1.5])

    with col_scores:
        section_label("SCORE BREAKDOWN (7 COMPONENTS)")
        breakdown_fig = score_breakdown_chart(components)
        st.plotly_chart(breakdown_fig, use_container_width=True, config={"displayModeBar": False})
        render_score_breakdown(components)

    with col_skills:
        section_label("SKILL COVERAGE")
        skill_fig = skill_match_chart(skill_gap)
        st.plotly_chart(skill_fig, use_container_width=True, config={"displayModeBar": False})

        # Skill Gap Detail
        _render_skill_gap_summary(skill_gap)

    st.markdown("---")

    # ── BOTTOM: Additional Metrics ─────────────────────────────────────────
    col_a, col_b, col_c, col_d = st.columns(4)
    with col_a:
        bm = components.get("behavioral_multiplier", 1.0)
        st.metric("Behavior Score", f"{bm:.2f}×")
    with col_b:
        avail = components.get("availability", 0)
        st.metric("Availability Score", f"{avail:.0%}")
    with col_c:
        trust = components.get("trust_score", 0)
        st.metric("Trust Score", f"{trust:.0%}")
    with col_d:
        career_match = components.get("career", 0)
        st.metric("Career Match", f"{career_match:.0%}")

    st.markdown("---")

    # ── AI Insights Panel ─────────────────────────────────────────────────
    section_label("AI INSIGHTS")
    insights = generate_ai_insights(candidate, components)
    render_ai_insights(insights)

    st.markdown("---")

    # ── AI Reasoning ──────────────────────────────────────────────────────
    section_label("RANKING REASONING")
    from core.reasoning import generate_reasoning
    reasoning = generate_reasoning(candidate, rank, components)
    st.markdown(
        f'<div style="background:#F5F5F7;border-radius:10px;padding:1.25rem;font-size:0.9375rem;color:#1D1D1F;line-height:1.6">'
        f'<span style="font-size:0.75rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.08em;display:block;margin-bottom:0.5rem">APTIVA AI Generated</span>'
        f'{reasoning}</div>',
        unsafe_allow_html=True,
    )

    # ── Navigation ────────────────────────────────────────────────────────
    st.markdown("---")
    nc1, nc2, nc3 = st.columns(3)
    with nc1:
        if st.button("👤 Full Profile", use_container_width=True):
            state["page"] = "candidate_profile"
            st.rerun()
    with nc2:
        if st.button("🧑‍⚖️ Judge Mode", use_container_width=True):
            state["page"] = "judge_mode"
            st.rerun()
    with nc3:
        if st.button("🏆 Back to Rankings", use_container_width=True):
            state["page"] = "home"
            st.rerun()


def _get_selected_result(state: dict):
    """Find the selected candidate in results."""
    results = state.get("results", [])
    selected_id = state.get("selected_candidate_id")

    if not selected_id and results:
        return results[0]  # Default to top candidate

    for r in results:
        if r["candidate"].get("candidate_id") == selected_id:
            return r
    return results[0] if results else None


def _render_skill_gap_summary(skill_gap: dict):
    """Render a concise skill gap summary."""
    present = skill_gap.get("present_core_skills", [])
    missing = skill_gap.get("missing_core_skills", [])
    bonus   = skill_gap.get("bonus_skills_matched", [])

    st.markdown(
        f"""
<div style="margin-top:0.75rem">
  <div style="font-size:0.75rem;font-weight:600;color:#1A8917;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.375rem">
    ✓ Core Skills Present ({len(present)})
  </div>
  <div style="margin-bottom:0.75rem">
    {"".join(f'<span class="skill-tag skill-tag-present">{s}</span>' for s in present[:6])}
    {"" if len(present) <= 6 else f'<span style="font-size:0.75rem;color:#6E6E73"> +{len(present)-6} more</span>'}
  </div>
  <div style="font-size:0.75rem;font-weight:600;color:#CC0000;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.375rem">
    ✗ Missing Core Skills ({len(missing)})
  </div>
  <div style="margin-bottom:0.75rem">
    {"".join(f'<span class="skill-tag skill-tag-missing">{s}</span>' for s in missing[:6])}
  </div>
  <div style="font-size:0.75rem;font-weight:600;color:#5E35B1;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.375rem">
    ✦ Bonus Skills ({len(bonus)})
  </div>
  <div>
    {"".join(f'<span class="skill-tag skill-tag-bonus">{s}</span>' for s in bonus[:5])}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
