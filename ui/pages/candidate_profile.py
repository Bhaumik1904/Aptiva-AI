"""
APTIVA AI — Candidate Profile Deep Dive
Full profile card, career timeline, skill list, education, and all signals.
"""

import streamlit as st

from core.reasoning import generate_ai_insights, generate_reasoning
from core.skill_gap import analyze_skill_gap
from ui.charts import behavioral_radar, skill_match_chart
from ui.components import (
    render_ai_insights,
    render_hireability_index,
    render_honeypot_warning,
    render_profile_header,
    render_score_breakdown,
)
from ui.icons import icon
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the full Candidate Profile page."""
    page_header("Candidate Profile", "Full profile deep dive")

    # -- Candidate Selector ------------------------------------------------
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
            "Select Candidate",
            list(candidate_options.keys()),
            index=next((i for i, v in enumerate(candidate_options.values()) if v == state.get("selected_candidate_id")), 0),
            key="profile_select",
        )
        if new_selection:
            new_cid = candidate_options[new_selection]
            if new_cid != state.get("selected_candidate_id"):
                st.session_state["selected_candidate_id"] = new_cid
                st.rerun()

    result = _get_selected_result(state)
    if not result:
        st.info("Select a candidate from the Rankings page to view their profile.")
        return

    candidate = result["candidate"]
    components = result.get("components", {})
    rank = result["rank"]

    profile = candidate.get("profile", {})
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    education = candidate.get("education", [])
    certifications = candidate.get("certifications", [])

    honeypot_flags = components.get("honeypot_flags", [])
    if honeypot_flags:
        render_honeypot_warning(honeypot_flags)

    render_profile_header(candidate, components, rank)

    st.markdown("<br>", unsafe_allow_html=True)

    # -- Tabs --------------------------------------------------------------
    tab_overview, tab_career, tab_skills, tab_signals, tab_reasoning = st.tabs([
        "Overview", "Career History", "Skills & Gap", "Behavioral Signals", "AI Reasoning"
    ])

    # -- TAB 1: Overview ---------------------------------------------------
    with tab_overview:
        col1, col2 = st.columns([1, 1.5])
        with col1:
            section_label("HIREABILITY INDEX")
            hi = components.get("hireability_index", {})
            render_hireability_index(hi)

            section_label("SCORE BREAKDOWN")
            render_score_breakdown(components)

        with col2:
            section_label("PROFILE SUMMARY")
            summary = profile.get("summary", "No summary available.")
            st.markdown(
                f'<div style="font-size:0.9375rem;color:#1D1D1F;line-height:1.65;background:#F5F5F7;border-radius:10px;padding:1.25rem">{summary}</div>',
                unsafe_allow_html=True,
            )

            # Quick stats
            st.markdown("<br>", unsafe_allow_html=True)
            section_label("QUICK FACTS")
            qc1, qc2 = st.columns(2)
            with qc1:
                st.markdown(_stat("Current Company", profile.get("current_company", "—")), unsafe_allow_html=True)
                st.markdown(_stat("Industry", profile.get("current_industry", "—")), unsafe_allow_html=True)
                st.markdown(_stat("Company Size", profile.get("current_company_size", "—")), unsafe_allow_html=True)
                st.markdown(_stat("Location", profile.get("location", "—")), unsafe_allow_html=True)
            with qc2:
                st.markdown(_stat("Notice Period", f"{signals.get('notice_period_days', '—')} days"), unsafe_allow_html=True)
                st.markdown(_stat("Open to Work", "Yes" if signals.get("open_to_work_flag") else "No"), unsafe_allow_html=True)
                st.markdown(_stat("Work Mode Preference", signals.get("preferred_work_mode", "—")), unsafe_allow_html=True)
                st.markdown(_stat("Willing to Relocate", "Yes" if signals.get("willing_to_relocate") else "No"), unsafe_allow_html=True)

    # -- TAB 2: Career History ---------------------------------------------
    with tab_career:
        if not career:
            st.info("No career history available.")
        else:
            section_label(f"CAREER HISTORY ({len(career)} roles)")
            for i, job in enumerate(sorted(career, key=lambda j: j.get("start_date", ""), reverse=True)):
                _render_job_card(job, i)

    # -- TAB 3: Skills & Gap -----------------------------------------------
    with tab_skills:
        skill_gap = analyze_skill_gap(candidate)

        sc1, sc2 = st.columns([1.2, 1.8])
        with sc1:
            skill_fig = skill_match_chart(skill_gap)
            st.plotly_chart(skill_fig, use_container_width=True, config={"displayModeBar": False})

            st.metric("Core Match", f"{skill_gap.get('core_match_pct', 0):.0f}%")
            st.metric("Bonus Match", f"{skill_gap.get('bonus_match_pct', 0):.0f}%")

        with sc2:
            # Skill gap detail table
            section_label("REQUIRED SKILLS ANALYSIS")
            required = skill_gap.get("required_skills", [])
            for skill_row in required:
                _render_skill_row(skill_row)

            st.markdown("<br>", unsafe_allow_html=True)
            section_label("BONUS SKILLS MATCHED")
            bonus = skill_gap.get("bonus_skills_matched", [])
            if bonus:
                st.markdown(
                    " ".join(f'<span class="skill-tag skill-tag-bonus">{s}</span>' for s in bonus),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<span style="color:#86868B;font-size:0.875rem">None matched</span>', unsafe_allow_html=True)

        # All candidate skills
        st.markdown("---")
        section_label("ALL CANDIDATE SKILLS")
        prof_colors = {"expert": "#1A8917", "advanced": "#0071E3", "intermediate": "#C47000", "beginner": "#CC0000"}
        cols = st.columns(3)
        for i, skill in enumerate(sorted(skills, key=lambda s: s.get("duration_months", 0), reverse=True)):
            with cols[i % 3]:
                pc = prof_colors.get(skill.get("proficiency", "intermediate"), "#6E6E73")
                st.markdown(
                    f"""
<div style="background:#F5F5F7;border-radius:8px;padding:0.625rem 0.875rem;margin:0.25rem 0;display:flex;justify-content:space-between;align-items:center">
  <span style="font-size:0.875rem;font-weight:500;color:#1D1D1F">{skill.get('name','')}</span>
  <span style="font-size:0.75rem;font-weight:600;color:{pc}">{skill.get('proficiency','').capitalize()}</span>
</div>""",
                    unsafe_allow_html=True,
                )

    # -- TAB 4: Behavioral Signals ------------------------------------------
    with tab_signals:
        bc1, bc2 = st.columns([1.5, 1.5])
        with bc1:
            radar_fig = behavioral_radar(signals)
            st.plotly_chart(radar_fig, use_container_width=True, config={"displayModeBar": False})

        with bc2:
            section_label("ALL 23 SIGNALS")
            _render_signals_table(signals)

        # Education
        st.markdown("---")
        section_label("EDUCATION")
        for edu in education:
            tier = edu.get("tier", "unknown")
            tier_color = {"tier_1": "#1A8917", "tier_2": "#0071E3", "tier_3": "#C47000", "tier_4": "#86868B"}.get(tier, "#86868B")
            st.markdown(
                f"""
<div class="aptiva-card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <div style="font-weight:600;color:#1D1D1F">{edu.get('degree','')} in {edu.get('field_of_study','')}</div>
      <div style="color:#6E6E73;font-size:0.875rem">{edu.get('institution','')} · {edu.get('start_year','?')} – {edu.get('end_year','?')}</div>
    </div>
    <span style="font-size:0.75rem;font-weight:600;color:{tier_color};background:{'#EBF5EA' if tier=='tier_1' else '#F5F5F7'};padding:0.2rem 0.6rem;border-radius:4px">{tier.upper()}</span>
  </div>
</div>""",
                unsafe_allow_html=True,
            )

    # -- TAB 5: AI Reasoning ------------------------------------------------
    with tab_reasoning:
        # AI Insights
        insights = generate_ai_insights(candidate, components)
        section_label("AI INSIGHTS")
        render_ai_insights(insights)

        st.markdown("---")

        section_label("APTIVA AI REASONING")
        reasoning = generate_reasoning(candidate, rank, components)
        st.markdown(
            f'<div style="background:#F5F5F7;border-radius:10px;padding:1.25rem;font-size:0.9375rem;color:#1D1D1F;line-height:1.6">{reasoning}</div>',
            unsafe_allow_html=True,
        )

        # Navigate to Judge Mode
        st.markdown("---")
        if st.button("Open in Judge Mode", use_container_width=False, icon=":material/gavel:"):
            state["page"] = "judge_mode"
            st.rerun()


# -- Helper Functions ----------------------------------------------------------

def _get_selected_result(state: dict):
    results = state.get("results", [])
    selected_id = state.get("selected_candidate_id")
    if not selected_id and results:
        return results[0]
    for r in results:
        if r["candidate"].get("candidate_id") == selected_id:
            return r
    return results[0] if results else None


def _stat(label: str, value: str) -> str:
    return f'<div style="margin:0.375rem 0"><span style="font-size:0.75rem;color:#86868B;font-weight:500">{label}</span><div style="font-size:0.875rem;color:#1D1D1F;font-weight:500">{value}</div></div>'


def _render_job_card(job: dict, index: int):
    is_current = job.get("is_current", False)
    current_badge = '<span style="background:#EBF5EA;color:#1A8917;font-size:0.7rem;font-weight:600;padding:0.15rem 0.5rem;border-radius:4px;margin-left:0.5rem">Current</span>' if is_current else ""
    duration = job.get("duration_months", 0)
    duration_str = f"{duration // 12}yr {duration % 12}mo" if duration >= 12 else f"{duration}mo"

    desc = job.get("description", "")
    with st.expander(f"**{job.get('title','')}** at {job.get('company','')} · {duration_str}", expanded=(index == 0)):
        st.markdown(
            f'<div style="display:flex;gap:1.5rem;font-size:0.8125rem;color:#86868B;margin-bottom:0.75rem">'
            f'<span style="display:inline-flex;align-items:center;gap:0.3rem">{icon("calendar",13)} {job.get("start_date","?")[:7]} → {job.get("end_date","Present")[:7] if job.get("end_date") else "Present"}</span>'
            f'<span style="display:inline-flex;align-items:center;gap:0.3rem">{icon("building",13)} {job.get("company_size","?")}</span>'
            f'<span style="display:inline-flex;align-items:center;gap:0.3rem">{icon("factory",13)} {job.get("industry","?")}</span>'
            f'</div><div style="font-size:0.9rem;color:#1D1D1F;line-height:1.65">{desc}</div>',
            unsafe_allow_html=True,
        )


def _render_skill_row(skill_row: dict):
    status = skill_row["status"]
    name = skill_row["name"]
    prof = skill_row.get("proficiency") or ""
    dur = skill_row.get("duration_months") or 0
    assessment = skill_row.get("assessment_score")
    mq = skill_row.get("match_quality", 0)

    if status == "present":
        _icon_svg = icon("check", 13, "#1A8917")
        icon_color = "#1A8917"
        bg = "#F5FFF5"
        prof_str = f"{prof.capitalize()} · {dur}mo"
        if assessment is not None:
            prof_str += f" · Assessed: {assessment:.0f}"
    else:
        _icon_svg = icon("x", 13, "#CC0000")
        icon_color = "#CC0000"
        bg = "#FFF5F5"
        prof_str = "Not found"

    st.markdown(
        f'<div style="background:{bg};border-radius:6px;padding:0.5rem 0.75rem;margin:0.25rem 0;display:flex;justify-content:space-between;align-items:center">'
        f'<div style="display:flex;align-items:center;gap:0.5rem">{_icon_svg}<span style="font-size:0.875rem;font-weight:500;color:#1D1D1F">{name}</span></div>'
        f'<span style="font-size:0.75rem;color:#6E6E73">{prof_str}</span></div>',
        unsafe_allow_html=True,
    )


def _render_signals_table(signals: dict):
    """Render key behavioral signals as a clean table."""
    items = [
        ("Profile Completeness", f"{signals.get('profile_completeness_score', 0)}/100"),
        ("Open to Work", "Yes" if signals.get("open_to_work_flag") else "No"),
        ("Last Active", signals.get("last_active_date", "—")),
        ("Notice Period", f"{signals.get('notice_period_days', 0)} days"),
        ("Recruiter Response Rate", f"{signals.get('recruiter_response_rate', 0):.0%}"),
        ("Avg Response Time", f"{signals.get('avg_response_time_hours', 0):.0f} hours"),
        ("Interview Completion", f"{signals.get('interview_completion_rate', 0):.0%}"),
        ("GitHub Activity", str(signals.get("github_activity_score", -1))),
        ("Saved by Recruiters (30d)", str(signals.get("saved_by_recruiters_30d", 0))),
        ("Profile Views (30d)", str(signals.get("profile_views_received_30d", 0))),
        ("Applications (30d)", str(signals.get("applications_submitted_30d", 0))),
        ("Email Verified", "Yes" if signals.get("verified_email") else "No"),
        ("Phone Verified", "Yes" if signals.get("verified_phone") else "No"),
        ("LinkedIn", "Connected" if signals.get("linkedin_connected") else "Not connected"),
        ("Connection Count", str(signals.get("connection_count", 0))),
        ("Willing to Relocate", "Yes" if signals.get("willing_to_relocate") else "No"),
        ("Work Mode Preference", signals.get("preferred_work_mode", "—")),
        ("Offer Acceptance Rate", f"{signals.get('offer_acceptance_rate', -1):.0%}" if signals.get("offer_acceptance_rate", -1) != -1 else "No history"),
    ]
    for label, value in items:
        st.markdown(
            f'<div style="display:flex;justify-content:space-between;padding:0.375rem 0;border-bottom:1px solid #F0F0F0;font-size:0.875rem"><span style="color:#6E6E73">{label}</span><span style="font-weight:500;color:#1D1D1F">{value}</span></div>',
            unsafe_allow_html=True,
        )
