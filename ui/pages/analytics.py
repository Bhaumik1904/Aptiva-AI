"""
APTIVA AI — Analytics Dashboard
Dataset-wide analytics: skill distributions, locations, experience,
behavior signals, Final Score distribution (ranking metric),
Hireability Index distribution (secondary metric), and recruiter readiness.
"""

import streamlit as st

from ui.charts import (
    experience_distribution,
    final_score_distribution,
    hireability_distribution,
    location_distribution,
    top_skills_chart,
)
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the Analytics Dashboard."""
    page_header(
        "Analytics",
        "Dataset-wide insights across all analyzed candidates",
    )

    results = state.get("results", [])
    candidates = [r["candidate"] for r in results]

    if not candidates:
        st.info("Run the ranking analysis first to see analytics.")
        return

    total = state.get("total_candidates", len(candidates))

    # -- Summary Stats ------------------------------------------------------
    section_label("DATASET OVERVIEW")
    s1, s2, s3, s4, s5, s6 = st.columns(6)

    yoe_values = [c["profile"].get("years_of_experience", 0) for c in candidates]
    hi_scores = [
        r.get("components", {}).get("hireability_index", {}).get("overall", 0)
        for r in results
        if r.get("components", {}).get("hireability_index")
    ]
    fs_scores = [r.get("score", 0) for r in results if "score" in r]
    avg_fs = sum(fs_scores) / max(1, len(fs_scores))
    open_to_work = sum(1 for c in candidates if c.get("redrob_signals", {}).get("open_to_work_flag", False))
    strong_hires = sum(1 for r in results if r.get("components", {}).get("recommendation") == "STRONG_YES")

    with s1:
        st.metric("Total Analyzed", f"{total:,}")
    with s2:
        st.metric("In Top Rankings", len(candidates))
    with s3:
        st.metric("Avg Experience", f"{sum(yoe_values)/max(1,len(yoe_values)):.1f} yrs")
    with s4:
        st.metric("Open to Work", open_to_work)
    with s5:
        st.metric("Avg Final Score", f"{avg_fs:.4f}", delta="Ranking metric")
    with s6:
        avg_hi = sum(hi_scores) / max(1, len(hi_scores))
        st.metric("Avg Hireability", f"{avg_hi:.0f}/100", delta="Secondary signal")

    st.markdown("---")

    # -- Row 1: Skills + Location --------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        section_label("TOP SKILLS DISTRIBUTION")
        skills_fig = top_skills_chart(candidates, top_n=12)
        st.plotly_chart(skills_fig, use_container_width=True, config={"displayModeBar": False})

    with col2:
        section_label("TOP CANDIDATE LOCATIONS")
        loc_fig = location_distribution(candidates)
        st.plotly_chart(loc_fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # -- Row 2: Final Score Distribution (primary) + Experience ------------
    col3, col4 = st.columns(2)

    with col3:
        section_label("FINAL SCORE DISTRIBUTION (RANKING METRIC)")
        fs_fig = final_score_distribution(results)
        st.plotly_chart(fs_fig, use_container_width=True, config={"displayModeBar": False})

    with col4:
        section_label("EXPERIENCE DISTRIBUTION")
        exp_fig = experience_distribution(candidates)
        st.plotly_chart(exp_fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # -- Row 2b: HI Distribution (secondary) ----------------------------
    section_label("HIREABILITY INDEX DISTRIBUTION (SECONDARY METRIC)")
    hi_fig = hireability_distribution(results)
    st.plotly_chart(hi_fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # -- Row 3: Behavior & Recommendations ---------------------------------
    section_label("RECOMMENDATION BREAKDOWN")
    rec_counts = {"STRONG_YES": 0, "YES": 0, "MAYBE": 0, "NO": 0}
    for r in results:
        rec = r.get("components", {}).get("recommendation", "MAYBE")
        rec_counts[rec] = rec_counts.get(rec, 0) + 1

    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        st.metric("Strong Hire", rec_counts["STRONG_YES"], delta="Top priority")
    with rc2:
        st.metric("Hire", rec_counts["YES"])
    with rc3:
        st.metric("Maybe", rec_counts["MAYBE"])
    with rc4:
        st.metric("Pass", rec_counts["NO"])

    st.markdown("---")

    # -- Behavior Distribution ----------------------------------------------
    section_label("BEHAVIOR SIGNAL DISTRIBUTION (TOP CANDIDATES)")
    bc1, bc2, bc3 = st.columns(3)

    notices = [c.get("redrob_signals", {}).get("notice_period_days", 0) for c in candidates]
    response_rates = [c.get("redrob_signals", {}).get("recruiter_response_rate", 0) for c in candidates]
    github_scores = [s for c in candidates for s in [c.get("redrob_signals", {}).get("github_activity_score", -1)] if s != -1]

    with bc1:
        import plotly.graph_objects as go
        fig_notice = go.Figure(go.Histogram(
            x=notices, nbinsx=10,
            marker={"color": "#0071E3", "line": {"color": "#FFFFFF", "width": 1}},
        ))
        fig_notice.update_layout(
            height=220,
            title={"text": "Notice Period Distribution", "font": {"size": 12, "color": "#6E6E73"}},
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 10, "r": 10, "t": 35, "b": 10},
            font_family="-apple-system,'Inter',sans-serif",
            xaxis={"title": "Days", "showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "#F0F0F0"},
        )
        st.plotly_chart(fig_notice, use_container_width=True, config={"displayModeBar": False})

    with bc2:
        fig_rr = go.Figure(go.Histogram(
            x=[r * 100 for r in response_rates], nbinsx=10,
            marker={"color": "#1A8917", "line": {"color": "#FFFFFF", "width": 1}},
        ))
        fig_rr.update_layout(
            height=220,
            title={"text": "Recruiter Response Rate", "font": {"size": 12, "color": "#6E6E73"}},
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 10, "r": 10, "t": 35, "b": 10},
            font_family="-apple-system,'Inter',sans-serif",
            xaxis={"title": "%", "showgrid": False},
            yaxis={"showgrid": True, "gridcolor": "#F0F0F0"},
        )
        st.plotly_chart(fig_rr, use_container_width=True, config={"displayModeBar": False})

    with bc3:
        if github_scores:
            fig_gh = go.Figure(go.Histogram(
                x=github_scores, nbinsx=10,
                marker={"color": "#7B3FE4", "line": {"color": "#FFFFFF", "width": 1}},
            ))
            fig_gh.update_layout(
                height=220,
                title={"text": "GitHub Activity Score", "font": {"size": 12, "color": "#6E6E73"}},
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin={"l": 10, "r": 10, "t": 35, "b": 10},
                font_family="-apple-system,'Inter',sans-serif",
                xaxis={"title": "Score", "showgrid": False},
                yaxis={"showgrid": True, "gridcolor": "#F0F0F0"},
            )
            st.plotly_chart(fig_gh, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # -- Recruiter Readiness Metrics ----------------------------------------
    section_label("RECRUITER READINESS METRICS")
    rr1, rr2, rr3, rr4, rr5 = st.columns(5)

    verified_both = sum(
        1 for c in candidates
        if c.get("redrob_signals", {}).get("verified_email") and c.get("redrob_signals", {}).get("verified_phone")
    )
    avg_notice = sum(notices) / max(1, len(notices))
    high_response = sum(1 for c in candidates if c.get("redrob_signals", {}).get("recruiter_response_rate", 0) >= 0.5)
    linkedin_connected = sum(1 for c in candidates if c.get("redrob_signals", {}).get("linkedin_connected", False))
    has_github = sum(1 for c in candidates if c.get("redrob_signals", {}).get("github_activity_score", -1) != -1)

    with rr1:
        st.metric("Fully Verified", f"{verified_both}/{len(candidates)}", delta="Email + Phone")
    with rr2:
        st.metric("Avg Notice Period", f"{avg_notice:.0f} days")
    with rr3:
        st.metric("High Response Rate", f"{high_response}/{len(candidates)}", delta=">=50% response")
    with rr4:
        st.metric("LinkedIn Connected", f"{linkedin_connected}/{len(candidates)}")
    with rr5:
        st.metric("Has GitHub", f"{has_github}/{len(candidates)}")

    st.markdown("---")

    # -- Top Industries -----------------------------------------------------
    section_label("TOP INDUSTRIES")
    from collections import Counter
    industry_counts: Counter = Counter()
    for c in candidates:
        for job in c.get("career_history", []):
            ind = job.get("industry", "")
            if ind:
                industry_counts[ind] += 1

    if industry_counts:
        top_ind = industry_counts.most_common(10)
        import plotly.graph_objects as go
        fig_ind = go.Figure(go.Bar(
            x=[t[1] for t in top_ind],
            y=[t[0] for t in top_ind],
            orientation="h",
            marker={"color": "#0071E3", "opacity": 0.8},
        ))
        fig_ind.update_layout(
            height=280,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
            font_family="-apple-system,'Inter',sans-serif",
            xaxis={"showgrid": False},
            yaxis={"showgrid": False},
        )
        st.plotly_chart(fig_ind, use_container_width=True, config={"displayModeBar": False})
