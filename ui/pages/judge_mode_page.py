"""
APTIVA AI — Judge Mode Page
Simulates how a senior recruiter or hackathon judge evaluates a candidate.
The most demo-friendly feature — shows APTIVA AI's reasoning depth.
"""

import streamlit as st

from core.judge_mode import generate_judge_verdict
from ui.components import render_hireability_index, render_profile_header
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the Judge Mode page."""
    page_header(
        "Judge Mode",
        "Simulate how a senior recruiter evaluates this candidate · APTIVA AI",
        "🧑‍⚖️",
    )

    # ── Candidate Selection ───────────────────────────────────────────────
    results = state.get("results", [])
    candidate_options = {
        f"#{r['rank']} · {r['candidate']['candidate_id']} · {r['candidate']['profile'].get('current_title','')[:30]}": r["candidate"]["candidate_id"]
        for r in results
    }
    
    col_title, col_sel = st.columns([2, 1])
    with col_sel:
        new_selection = st.selectbox(
            "Select Candidate to Judge", list(candidate_options.keys()),
            index=next((i for i, v in enumerate(candidate_options.values()) if v == state.get("selected_candidate_id")), 0),
            key="judge_select",
        )
        if new_selection:
            new_cid = candidate_options[new_selection]
            if new_cid != state.get("selected_candidate_id"):
                st.session_state["selected_candidate_id"] = new_cid  # Fix: update session_state directly
                st.rerun()

    result = _get_selected_result(state)
    if not result:
        st.info("Select a candidate from the Rankings page to activate Judge Mode.")
        return

    candidate = result["candidate"]
    components = result.get("components", {})
    rank = result["rank"]

    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})

    # ── Profile Header ────────────────────────────────────────────────────
    render_profile_header(candidate, components, rank)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Generate Verdict ──────────────────────────────────────────────────
    with st.spinner("Generating judge evaluation..."):
        verdict = generate_judge_verdict(candidate, components, rank)

    # ── Verdict Banner ────────────────────────────────────────────────────
    label = verdict.get("verdict_label", "Maybe")
    label_styles = {
        "Strong Hire": ("verdict-strong-hire", "✦ Strong Hire", "#1A8917"),
        "Hire":        ("verdict-hire",        "✓ Hire",        "#1565C0"),
        "Maybe":       ("verdict-maybe",       "◈ Maybe",       "#C47000"),
        "Pass":        ("verdict-pass",        "✗ Pass",        "#CC0000"),
    }
    cls, txt, color = label_styles.get(label, ("verdict-maybe", "◈ Maybe", "#C47000"))
    interview_rec = verdict.get("interview_recommendation", "MAYBE")

    st.markdown(
        f"""
<div class="{cls}" style="margin-bottom:1.25rem;border-radius:10px">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <div style="font-size:1.5rem;font-weight:800;color:{color};letter-spacing:-0.02em">{txt}</div>
      <div style="font-size:0.9375rem;color:#1D1D1F;margin-top:0.25rem">{verdict.get('final_verdict','')}</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:0.625rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em">Interview?</div>
      <div style="font-size:1.25rem;font-weight:800;color:{color}">{interview_rec}</div>
      <div style="font-size:0.75rem;color:#86868B">Confidence: {verdict.get('judge_confidence', 0):.0%}</div>
    </div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # ── Two-Column Layout ─────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        # Why Recommended
        section_label("WHY RECOMMENDED")
        _verdict_card(verdict.get("why_recommended", "—"), icon="✓", color="#1A8917")

        st.markdown("<br>", unsafe_allow_html=True)

        # Biggest Strength
        section_label("BIGGEST STRENGTH")
        _verdict_card(verdict.get("biggest_strength", "—"), icon="⭑", color="#0071E3")

        st.markdown("<br>", unsafe_allow_html=True)

        # Risk Factors
        section_label("RISK FACTORS")
        risks = verdict.get("risk_factors", [])
        for risk in risks:
            st.markdown(
                f'<div style="background:#FFF5F5;border-left:3px solid #CC0000;padding:0.625rem 0.875rem;border-radius:0 6px 6px 0;font-size:0.875rem;color:#1D1D1F;margin:0.375rem 0">{risk}</div>',
                unsafe_allow_html=True,
            )

    with col2:
        # Section label adapts for Rank #1 — 'Why Not Ranked Higher' is
        # semantically correct for ranks 2-100 but misleading for the
        # top-ranked candidate who has no candidate above them.
        why_label = "PLACEMENT RATIONALE" if rank == 1 else "WHY NOT RANKED HIGHER"
        section_label(why_label)
        _verdict_card(verdict.get("why_not_ranked_higher", "—"), icon="↓", color="#C47000")

        st.markdown("<br>", unsafe_allow_html=True)

        # Biggest Weakness
        section_label("BIGGEST WEAKNESS")
        _verdict_card(verdict.get("biggest_weakness", "—"), icon="!", color="#CC0000")

        st.markdown("<br>", unsafe_allow_html=True)

        # Hireability Index in compact form
        section_label("HIREABILITY INDEX™")
        hi = components.get("hireability_index", {})
        render_hireability_index(hi, compact=False)

    st.markdown("---")

    # ── Final Verdict Box ─────────────────────────────────────────────────
    section_label("FINAL VERDICT")
    hi = components.get("hireability_index", {})
    hi_score = hi.get("overall", 0) if hi else 0
    # Issue #8: Final Score added as the primary (first) metric in the verdict box.
    final_score_display = components.get("final_score", 0)

    final_color = "#1A8917" if label == "Strong Hire" else "#0071E3" if label == "Hire" else "#C47000" if label == "Maybe" else "#CC0000"
    final_bg = "#EBF5EA" if label == "Strong Hire" else "#E3F2FD" if label == "Hire" else "#FFF3E0" if label == "Maybe" else "#FFEBEB"

    st.markdown(
        f"""
<div style="background:{final_bg};border-radius:14px;padding:2rem;text-align:center">
  <div style="font-size:0.6875rem;font-weight:600;color:{final_color};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.75rem">APTIVA AI Judge Mode Verdict</div>
  <div style="font-size:3rem;font-weight:800;color:{final_color};letter-spacing:-0.03em;margin-bottom:0.5rem">{txt}</div>
  <div style="display:flex;justify-content:center;gap:2.5rem;margin-top:1rem">
    <div style="text-align:center">
      <div style="font-size:1.5rem;font-weight:700;color:{final_color}">{final_score_display:.4f}</div>
      <div style="font-size:0.7rem;color:#86868B;text-transform:uppercase">Final Score</div>
      <div style="font-size:0.65rem;color:#86868B;margin-top:0.1rem">(ranking metric)</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:1.5rem;font-weight:700;color:#1D1D1F">{hi_score:.0f}</div>
      <div style="font-size:0.7rem;color:#86868B;text-transform:uppercase">Hireability Index™</div>
      <div style="font-size:0.65rem;color:#86868B;margin-top:0.1rem">(recruiter trust, 0–100)</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:1.5rem;font-weight:700;color:#1D1D1F">#{rank}</div>
      <div style="font-size:0.7rem;color:#86868B;text-transform:uppercase">Overall Rank</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:1.5rem;font-weight:700;color:#1D1D1F">{verdict.get('judge_confidence', 0):.0%}</div>
      <div style="font-size:0.7rem;color:#86868B;text-transform:uppercase">Judge Confidence</div>
    </div>
    <div style="text-align:center">
      <div style="font-size:1.5rem;font-weight:700;color:{final_color}">{interview_rec}</div>
      <div style="font-size:0.7rem;color:#86868B;text-transform:uppercase">Interview?</div>
    </div>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    st.markdown("---")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_selected_result(state: dict):
    results = state.get("results", [])
    selected_id = state.get("selected_candidate_id")
    if not selected_id and results:
        return results[0]
    for r in results:
        if r["candidate"].get("candidate_id") == selected_id:
            return r
    return results[0] if results else None


def _verdict_card(text: str, icon: str, color: str):
    st.markdown(
        f"""
<div style="background:#F5F5F7;border-radius:10px;padding:1rem 1.25rem;display:flex;gap:0.75rem;align-items:flex-start">
  <span style="font-size:1rem;color:{color};font-weight:700;margin-top:0.125rem">{icon}</span>
  <div style="font-size:0.9375rem;color:#1D1D1F;line-height:1.6">{text}</div>
</div>""",
        unsafe_allow_html=True,
    )
