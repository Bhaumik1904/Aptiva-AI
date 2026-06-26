"""
APTIVA AI — Rankings Dashboard (Home Page)
The first page judges see. Shows ranked table with Hireability Index™,
filters, and immediate value demonstration.
"""

import pandas as pd
import streamlit as st

from ui.components import (
    recommendation_badge,
    render_empty_state,
    render_hireability_index,
)
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the Rankings Dashboard."""
    _ICON_TROPHY = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="26" height="26" viewBox="0 0 24 24" '
        'fill="none" stroke="#0071E3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/>'
        '<path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>'
        '<path d="M4 22h16"/>'
        '<path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/>'
        '<path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/>'
        '<path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/>'
        '</svg>'
    )
    page_header(
        "Candidate Rankings",
        "Top candidates ranked for Senior AI Engineer · Redrob AI",
        _ICON_TROPHY,
    )

    results = state.get("results", [])

    if not results:
        render_empty_state(
            "No ranking results yet",
            "Click 'Run Ranking' in the sidebar to analyze candidates.",
        )
        return

    # ── Summary Stats Bar ──────────────────────────────────────────────────
    total_analyzed = state.get("total_candidates", len(results))
    top_score = results[0]["score"] if results else 0
    avg_hi = sum(
        r["components"].get("hireability_index", {}).get("overall", 0)
        for r in results if r.get("components")
    ) / max(1, len(results))
    strong_yes = sum(1 for r in results if r.get("components", {}).get("recommendation") == "STRONG_YES")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Candidates Analyzed", f"{total_analyzed:,}")
    with c2:
        st.metric("In Rankings", len(results))
    with c3:
        st.metric("Top Score", f"{top_score:.4f}")
    with c4:
        st.metric("Avg Hireability", f"{avg_hi:.0f}/100")
    with c5:
        st.metric("Strong Hires", strong_yes)

    st.markdown("---")

    # ── Filters Row ───────────────────────────────────────────────────────
    with st.expander("🔍 Filters & Search", expanded=False):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)
        with fcol1:
            # Issue #4: filter on Final Score (ranking metric), not Hireability Index.
            # Min HI could suppress the top-ranked candidate if their HI < threshold.
            min_fs = st.slider("Min Final Score", 0.00, 1.00, 0.00, step=0.05,
                               help="Filters candidates by Final Score — the ranking metric.")
        with fcol2:
            yoe_range = st.slider("Years of Experience", 0, 20, (0, 20))
        with fcol3:
            title_filter = st.text_input("Title contains", placeholder="e.g. ML, NLP...")
        with fcol4:
            location_filter = st.text_input("Location contains", placeholder="e.g. Bangalore...")

        rec_filter = st.multiselect(
            "Recommendation",
            ["STRONG_YES", "YES", "MAYBE", "NO"],
            default=["STRONG_YES", "YES", "MAYBE", "NO"],
        )

    # ── Build Table Data ──────────────────────────────────────────────────
    rows = []
    for r in results:
        cand = r["candidate"]
        comp = r.get("components", {})
        profile = cand["profile"]
        signals = cand.get("redrob_signals", {})
        hi = comp.get("hireability_index", {})

        yoe = profile.get("years_of_experience", 0)
        title = profile.get("current_title", "")
        location = profile.get("location", "")
        rec = comp.get("recommendation", "MAYBE")
        hi_score = hi.get("overall", 0) if hi else 0

        # Apply filters
        if r["score"] < min_fs:  # Issue #4: gate on Final Score, not HI
            continue
        if not (yoe_range[0] <= yoe <= yoe_range[1]):
            continue
        if title_filter and title_filter.lower() not in title.lower():
            continue
        if location_filter and location_filter.lower() not in location.lower():
            continue
        if rec not in rec_filter:
            continue

        rows.append({
            "Rank":           r["rank"],
            "Candidate ID":   cand["candidate_id"],
            "Hireability™":   f"{hi_score:.0f}",
            "Score":          f"{r['score']:.4f}",
            "Recommendation": rec,
            "Title":          title,
            "YOE":            f"{yoe:.0f}yr",
            "Location":       location,
            "Notice":         f"{signals.get('notice_period_days',0)}d",
            "Open to Work":   "✓" if signals.get("open_to_work_flag") else "—",
            "_raw_rec":       rec,
            "_hi":            hi_score,
            "_cid":           cand["candidate_id"],
        })

    if not rows:
        render_empty_state("No candidates match current filters")
        return

    # ── Score Legend ───────────────────────────────────────────────────────
    st.markdown(
        """
<div style="background:#F0F7FF;border:1px solid #C8DEFF;border-radius:8px;padding:0.625rem 1rem;margin-bottom:0.75rem;display:flex;gap:2rem;flex-wrap:wrap">
  <div style="font-size:0.8125rem;color:#1D1D1F">
    <span style="font-weight:700;color:#0071E3">Score</span>
    <span style="color:#6E6E73"> — Ranking metric (drives submission order, optimised for NDCG)</span>
  </div>
  <div style="font-size:0.8125rem;color:#1D1D1F">
    <span style="font-weight:700;color:#1D1D1F">Hireability™</span>
    <span style="color:#6E6E73"> — Recruiter trust metric (5-dimension, 0–100)</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    section_label(f"SHOWING {len(rows)} CANDIDATES")

    # ── Render Table ──────────────────────────────────────────────────────
    # Display columns (hide internal keys)
    display_cols = ["Rank", "Candidate ID", "Hireability™", "Score", "Recommendation",
                    "Title", "YOE", "Location", "Notice", "Open to Work"]
    df = pd.DataFrame(rows)[display_cols]

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank":         st.column_config.NumberColumn("Rank", width="small"),
            "Hireability™": st.column_config.TextColumn(
                "Hireability™",
                width="small",
                help="Recruiter trust score (0–100). 5 dimensions: Technical Fit, Career Relevance, Behavior, Availability, Trust.",
            ),
            "Score":        st.column_config.TextColumn(
                "Score",
                width="small",
                help="Final Score (0–1.0): the ranking metric that determines position in submission.csv.",
            ),
        },
        height=min(600, 60 + len(rows) * 36),
    )

    # ── Candidate Selection ───────────────────────────────────────────────
    st.markdown("---")
    section_label("SELECT CANDIDATE TO ANALYZE")

    candidate_options = {
        f"#{r['Rank']} · {r['Candidate ID']} · {r['Title'][:35]} · HI {r['Hireability™']}": r["_cid"]
        for r in rows
    }

    selected_label = st.selectbox(
        "Choose a candidate",
        list(candidate_options.keys()),
        label_visibility="collapsed",
    )

    if selected_label:
        selected_cid = candidate_options[selected_label]
        st.session_state["selected_candidate_id"] = selected_cid  # persist across pages

        # ── Quick Action Buttons ─────────────────────────────────────────
        # SVG icons matching the sidebar (Lucide-style, 15×15, stroke)
        _BTN_CSS = """
<style>
.qa-btn-row { display:flex; gap:0.75rem; margin:0.5rem 0 0.1rem; }
.qa-btn {
  flex:1; display:flex; align-items:center; justify-content:center;
  gap:0.5rem; padding:0.5rem 0.75rem;
  background:#F5F5F7; border:1px solid #D2D2D7; border-radius:6px;
  font-size:0.875rem; font-weight:600; color:#1D1D1F;
  user-select:none;
  transition:background 0.12s, border-color 0.12s;
}
.qa-btn:hover { background:#E8F2FF; border-color:#0071E3; color:#0071E3; }
.qa-btn svg { flex-shrink:0; }
/* Invisible overlay buttons — same technique as sidebar */
.qa-wrapper [data-testid="stBaseButton-secondary"],
.qa-wrapper [data-testid="stBaseButton-primary"] {
  opacity: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  pointer-events: all !important;
  position: relative !important;
  z-index: 2 !important;
}
.qa-wrapper .stButton {
  margin-top: -2.25rem !important;
  margin-bottom: 0 !important;
}
</style>"""

        _ICON_PROFILE  = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
        _ICON_ANALYSIS = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
        _ICON_JUDGE    = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
        _ICON_COMPARE  = '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'

        st.markdown(
            f"""{_BTN_CSS}
<div class="qa-btn-row">
  <div class="qa-btn">{_ICON_PROFILE} View Profile</div>
  <div class="qa-btn">{_ICON_ANALYSIS} AI Analysis</div>
  <div class="qa-btn">{_ICON_JUDGE} Judge Mode</div>
  <div class="qa-btn">{_ICON_COMPARE} Add to Compare</div>
</div>""",
            unsafe_allow_html=True,
        )

        # Invisible Streamlit buttons overlaid for click capture
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("View Profile", use_container_width=True, key="home_view_profile"):
                st.session_state["page"] = "candidate_profile"
                st.rerun()
        with col2:
            if st.button("AI Analysis", use_container_width=True, key="home_ai_analysis"):
                st.session_state["page"] = "ai_analysis"
                st.rerun()
        with col3:
            if st.button("Judge Mode", use_container_width=True, key="home_judge_mode"):
                st.session_state["page"] = "judge_mode"
                st.rerun()
        with col4:
            if st.button("Add to Compare", use_container_width=True, key="home_compare"):
                compare = st.session_state.get("compare_list", [])
                if selected_cid in compare:
                    st.info(f"{selected_cid} is already in the comparison list.")
                elif len(compare) >= 2:
                    st.warning("Compare list is full (max 2). Remove a candidate first.")
                else:
                    compare.append(selected_cid)
                    st.session_state["compare_list"] = compare
                    slot = "Candidate A" if len(compare) == 1 else "Candidate B"
                    st.success(f"Added {selected_cid} as {slot}.")

    # ── Download ──────────────────────────────────────────────────────────
    st.markdown("---")
    if state.get("submission_csv"):
        st.download_button(
            "Download submission.csv",
            data=state["submission_csv"],
            file_name="submission.csv",
            mime="text/csv",
        )
