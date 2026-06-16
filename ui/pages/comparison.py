"""
APTIVA AI — Candidate Comparison Mode
Side-by-side enterprise comparison of two candidates with winner highlighting.
"""

import streamlit as st

from ui.charts import comparison_radar
from ui.components import render_hireability_index, render_recommendation_badge
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the Candidate Comparison page."""
    page_header(
        "Compare Candidates",
        "Side-by-side evaluation of two candidates",
        "⚖️",
    )

    results = state.get("results", [])
    if len(results) < 2:
        st.info("At least 2 ranked candidates are needed for comparison. Run the ranking first.")
        return

    # ── Candidate Selection ───────────────────────────────────────────────
    compare_list = state.get("compare_list", [])

    options = {
        f"#{r['rank']} · {r['candidate']['candidate_id']} · {r['candidate']['profile'].get('current_title','')[:30]}": r["candidate"]["candidate_id"]
        for r in results
    }

    section_label("SELECT CANDIDATES TO COMPARE")
    sel_col1, sel_col2 = st.columns(2)

    with sel_col1:
        default_a = next((k for k, v in options.items() if v == compare_list[0]), list(options.keys())[0]) if compare_list else list(options.keys())[0]
        sel_a_label = st.selectbox("Candidate A", list(options.keys()), index=list(options.keys()).index(default_a), key="cmp_a")
        cid_a = options[sel_a_label]

    with sel_col2:
        default_b_idx = min(1, len(list(options.keys())) - 1)
        if compare_list and len(compare_list) >= 2:
            b_key = next((k for k, v in options.items() if v == compare_list[1]), list(options.keys())[default_b_idx])
            default_b_idx = list(options.keys()).index(b_key)
        sel_b_label = st.selectbox("Candidate B", list(options.keys()), index=default_b_idx, key="cmp_b")
        cid_b = options[sel_b_label]

    if cid_a == cid_b:
        st.warning("Please select two different candidates.")
        return

    result_a = next((r for r in results if r["candidate"]["candidate_id"] == cid_a), None)
    result_b = next((r for r in results if r["candidate"]["candidate_id"] == cid_b), None)

    if not result_a or not result_b:
        st.error("Could not find selected candidates.")
        return

    cand_a = result_a["candidate"]
    cand_b = result_b["candidate"]
    comp_a = result_a.get("components", {})
    comp_b = result_b.get("components", {})

    hi_a = comp_a.get("hireability_index", {})
    hi_b = comp_b.get("hireability_index", {})
    hi_score_a = hi_a.get("overall", 0) if hi_a else 0
    hi_score_b = hi_b.get("overall", 0) if hi_b else 0

    winner_is_a = hi_score_a >= hi_score_b

    st.markdown("---")

    # ── Radar Chart ───────────────────────────────────────────────────────
    section_label("MULTI-DIMENSION COMPARISON")
    label_a = f"#{result_a['rank']} · {cand_a['profile'].get('current_title','')[:20]}"
    label_b = f"#{result_b['rank']} · {cand_b['profile'].get('current_title','')[:20]}"
    radar_fig = comparison_radar(comp_a, comp_b, label_a, label_b)
    st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # ── Side-by-Side Columns ──────────────────────────────────────────────
    section_label("HEAD-TO-HEAD")
    col_a, col_vs, col_b = st.columns([5, 1, 5])

    with col_a:
        _render_candidate_column(cand_a, comp_a, result_a, hi_score_a, is_winner=winner_is_a)

    with col_vs:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:1.25rem;font-weight:700;color:#86868B;padding-top:4rem">VS</div>',
            unsafe_allow_html=True,
        )

    with col_b:
        _render_candidate_column(cand_b, comp_b, result_b, hi_score_b, is_winner=not winner_is_a)

    st.markdown("---")

    # ── Detailed Comparison Table ─────────────────────────────────────────
    section_label("DETAILED COMPARISON")

    dimensions = [
        ("Title Match",         comp_a.get("title", 0),        comp_b.get("title", 0),        "%"),
        ("Skill Trust",         comp_a.get("skills", 0),       comp_b.get("skills", 0),       "%"),
        ("Career Substance",    comp_a.get("career", 0),       comp_b.get("career", 0),       "%"),
        ("Experience Fit",      comp_a.get("experience", 0),   comp_b.get("experience", 0),   "%"),
        ("Education",           comp_a.get("education", 0),    comp_b.get("education", 0),    "%"),
        ("Location",            comp_a.get("location", 0),     comp_b.get("location", 0),     "%"),
        ("Availability",        comp_a.get("availability", 0), comp_b.get("availability", 0), "%"),
        ("Trust Score",         comp_a.get("trust_score", 0),  comp_b.get("trust_score", 0),  "%"),
        ("Tech Fit (HI)",       hi_a.get("technical_fit", 0) / 100, hi_b.get("technical_fit", 0) / 100, "%"),
        ("Career Rel. (HI)",    hi_a.get("career_relevance", 0) / 100, hi_b.get("career_relevance", 0) / 100, "%"),
        ("Behavioral Mult.",    comp_a.get("behavioral_multiplier", 1.0) - 1, comp_b.get("behavioral_multiplier", 1.0) - 1, "×+"),
        ("Final Score",         result_a["score"],              result_b["score"],              "score"),
        ("Hireability Index™",  hi_score_a / 100,               hi_score_b / 100,               "hi"),
    ]

    for label, val_a, val_b, fmt in dimensions:
        _render_comparison_row(label, val_a, val_b, fmt)

    # ── Signals Side-by-Side ──────────────────────────────────────────────
    st.markdown("---")
    section_label("BEHAVIORAL SIGNALS")
    sig_col1, sig_col2 = st.columns(2)

    sig_a = cand_a.get("redrob_signals", {})
    sig_b = cand_b.get("redrob_signals", {})

    signal_rows = [
        ("Notice Period", f"{sig_a.get('notice_period_days',0)}d", f"{sig_b.get('notice_period_days',0)}d"),
        ("Last Active", sig_a.get("last_active_date","—"), sig_b.get("last_active_date","—")),
        ("Open to Work", "Yes" if sig_a.get("open_to_work_flag") else "No", "Yes" if sig_b.get("open_to_work_flag") else "No"),
        ("Response Rate", f"{sig_a.get('recruiter_response_rate',0):.0%}", f"{sig_b.get('recruiter_response_rate',0):.0%}"),
        ("GitHub Activity", str(sig_a.get("github_activity_score",-1)), str(sig_b.get("github_activity_score",-1))),
        ("Interview Rate", f"{sig_a.get('interview_completion_rate',0):.0%}", f"{sig_b.get('interview_completion_rate',0):.0%}"),
    ]

    with sig_col1:
        st.markdown(f'<div style="font-size:0.875rem;font-weight:600;color:#1D1D1F;margin-bottom:0.5rem">{label_a}</div>', unsafe_allow_html=True)
    with sig_col2:
        st.markdown(f'<div style="font-size:0.875rem;font-weight:600;color:#1D1D1F;margin-bottom:0.5rem">{label_b}</div>', unsafe_allow_html=True)

    for row_label, val_a, val_b in signal_rows:
        with sig_col1:
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #F0F0F0;font-size:0.8125rem"><span style="color:#6E6E73">{row_label}</span><strong>{val_a}</strong></div>', unsafe_allow_html=True)
        with sig_col2:
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:0.3rem 0;border-bottom:1px solid #F0F0F0;font-size:0.8125rem"><span style="color:#6E6E73">{row_label}</span><strong>{val_b}</strong></div>', unsafe_allow_html=True)

    # ── Winner Declaration ────────────────────────────────────────────────
    st.markdown("---")
    winner_result = result_a if winner_is_a else result_b
    winner_cand = cand_a if winner_is_a else cand_b
    winner_hi = hi_score_a if winner_is_a else hi_score_b
    winner_title = winner_cand["profile"].get("current_title", "")

    st.markdown(
        f"""
<div style="background:#EBF5EA;border:1.5px solid #1A8917;border-radius:14px;padding:1.5rem;text-align:center">
  <div style="font-size:0.75rem;font-weight:600;color:#1A8917;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Recommended Candidate</div>
  <div style="font-size:1.5rem;font-weight:700;color:#1D1D1F;letter-spacing:-0.02em">{winner_cand.get('candidate_id')} — {winner_title}</div>
  <div style="font-size:0.9375rem;color:#6E6E73;margin-top:0.25rem">Rank #{winner_result['rank']} · Hireability Index™ <strong style="color:#1A8917">{winner_hi:.0f}/100</strong> · Score {winner_result['score']:.4f}</div>
</div>""",
        unsafe_allow_html=True,
    )


# ── Helper Renders ────────────────────────────────────────────────────────────

def _render_candidate_column(candidate, components, result, hi_score, is_winner: bool):
    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    hi = components.get("hireability_index", {})
    rec = components.get("recommendation", "MAYBE")

    winner_style = "border:1.5px solid #1A8917;background:#F5FFF5;" if is_winner else "background:#F5F5F7;"
    winner_badge = '<span style="background:#1A8917;color:#FFFFFF;font-size:0.7rem;font-weight:700;padding:0.2rem 0.6rem;border-radius:20px;margin-left:0.5rem">Recommended</span>' if is_winner else ""

    st.markdown(
        f"""
<div style="{winner_style}border-radius:14px;padding:1.25rem;margin-bottom:0.75rem">
  <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
    <span style="font-size:0.75rem;font-weight:600;background:#E8F2FF;color:#0071E3;padding:0.2rem 0.6rem;border-radius:20px">Rank #{result['rank']}</span>
    {winner_badge}
  </div>
  <div style="font-size:1.125rem;font-weight:700;color:#1D1D1F;margin-bottom:0.25rem">{profile.get('current_title','')}</div>
  <div style="font-size:0.875rem;color:#6E6E73;margin-bottom:1rem">{profile.get('current_company','')} · {profile.get('location','')}</div>
  <div style="font-size:2.5rem;font-weight:800;color:{'#1A8917' if hi_score>=80 else '#0071E3' if hi_score>=65 else '#C47000' if hi_score>=50 else '#CC0000'};letter-spacing:-0.04em;line-height:1">{hi_score:.0f}</div>
  <div style="font-size:0.625rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:1rem">Hireability Index™</div>
  <div style="font-size:0.875rem;color:#6E6E73">Score: <strong style="color:#1D1D1F">{result['score']:.4f}</strong></div>
  <div style="font-size:0.875rem;color:#6E6E73">Experience: <strong>{profile.get('years_of_experience',0):.0f} years</strong></div>
  <div style="font-size:0.875rem;color:#6E6E73">Notice: <strong>{signals.get('notice_period_days',0)} days</strong></div>
</div>""",
        unsafe_allow_html=True,
    )
    render_recommendation_badge(rec)


def _render_comparison_row(label: str, val_a: float, val_b: float, fmt: str):
    """Render a single comparison row with winner highlighting."""
    if fmt == "hi":
        str_a = f"{val_a * 100:.0f}/100"
        str_b = f"{val_b * 100:.0f}/100"
    elif fmt == "score":
        str_a = f"{val_a:.4f}"
        str_b = f"{val_b:.4f}"
    elif fmt == "×+":
        str_a = f"+{val_a:.2f}×"
        str_b = f"+{val_b:.2f}×"
    else:
        str_a = f"{val_a * 100:.0f}%"
        str_b = f"{val_b * 100:.0f}%"

    a_wins = val_a >= val_b
    win_color_a = "#1A8917" if a_wins else "#1D1D1F"
    win_color_b = "#1A8917" if not a_wins else "#1D1D1F"
    win_weight_a = "700" if a_wins else "400"
    win_weight_b = "700" if not a_wins else "400"

    st.markdown(
        f"""
<div style="display:flex;align-items:center;padding:0.5rem 0;border-bottom:1px solid #F0F0F0">
  <div style="flex:1;text-align:right;font-size:0.9rem;font-weight:{win_weight_a};color:{win_color_a}">{str_a}</div>
  <div style="flex:1;text-align:center;font-size:0.75rem;color:#86868B;padding:0 1rem">{label}</div>
  <div style="flex:1;text-align:left;font-size:0.9rem;font-weight:{win_weight_b};color:{win_color_b}">{str_b}</div>
</div>""",
        unsafe_allow_html=True,
    )
