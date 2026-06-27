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
from ui.icons import icon
from ui.styles import page_header, section_label


def render(state: dict):
    """Render the Rankings Dashboard."""
    page_header(
        "Candidate Rankings",
        "Top candidates ranked for Senior AI Engineer · Redrob AI",
        icon("trophy", 26),
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
    with st.expander("Filters & Search", expanded=False):
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
            "Open to Work":   "Yes" if signals.get("open_to_work_flag") else "No",
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

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("View Profile", use_container_width=True, key="home_view_profile", icon=":material/person:"):
                st.session_state["page"] = "candidate_profile"
                st.rerun()
        with col2:
            if st.button("AI Analysis", use_container_width=True, key="home_ai_analysis", icon=":material/psychology:"):
                st.session_state["page"] = "ai_analysis"
                st.rerun()
        with col3:
            if st.button("Judge Mode", use_container_width=True, key="home_judge_mode", icon=":material/gavel:"):
                st.session_state["page"] = "judge_mode"
                st.rerun()
        with col4:
            if st.button("Add to Compare", use_container_width=True, key="home_compare", icon=":material/compare_arrows:"):
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
        SUBMISSION_FILENAME = "submission.csv"
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            recruiter_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "⬇ Download Recruiter Report",
                data=recruiter_csv,
                file_name="recruiter_report.csv",
                mime="text/csv",
                use_container_width=True,
            )
            
        with col_dl2:
            submission_data = state["submission_csv"]
            
            # Detect Demo Mode based on total dataset size (sample dataset has exactly 50 candidates)
            is_demo = state.get("total_candidates", 0) == 50
            
            if is_demo:
                st.info(
                    "**Demo Mode:** The official sample dataset contains 50 candidates. "
                    "The official competition submission CSV requires the complete 100,000-candidate dataset "
                    "and is therefore unavailable in Demo Mode."
                )
                st.button(
                    "⬇ Download Submission CSV",
                    disabled=True,
                    use_container_width=True,
                    help="Submission CSV is only available when running on the full 100,000-candidate dataset."
                )
            else:
                is_valid = True
                error_msg = ""
                
                try:
                    import io, csv
                    reader = list(csv.reader(io.StringIO(submission_data)))
                    if not reader:
                        is_valid = False
                        error_msg = "CSV is empty."
                    else:
                        header = reader[0]
                        expected_header = ["candidate_id", "rank", "score", "reasoning"]
                        if header != expected_header:
                            is_valid = False
                            error_msg = f"Invalid columns. Expected {expected_header}, got {header}."
                        else:
                            rows_data = reader[1:]
                            if len(rows_data) != 100:
                                is_valid = False
                                error_msg = f"Expected exactly 100 candidates, got {len(rows_data)}."
                            else:
                                candidate_ids = set()
                                for i, row in enumerate(rows_data):
                                    if len(row) != 4:
                                        is_valid = False
                                        error_msg = f"Row {i+1} does not have exactly 4 columns."
                                        break
                                    
                                    cid, r_rank, r_score, r_reason = row
                                    
                                    if cid in candidate_ids:
                                        is_valid = False
                                        error_msg = f"Duplicate candidate_id found: {cid}."
                                        break
                                    candidate_ids.add(cid)
                                    
                                    try:
                                        if int(r_rank) != i + 1:
                                            is_valid = False
                                            error_msg = f"Rank values out of order. Expected {i+1}, got {r_rank}."
                                            break
                                    except ValueError:
                                        is_valid = False
                                        error_msg = f"Invalid rank value at row {i+1}: {r_rank}."
                                        break
                except Exception as e:
                    is_valid = False
                    error_msg = f"Validation exception: {str(e)}"
                
                if is_valid:
                    st.download_button(
                        "⬇ Download Submission CSV",
                        data=submission_data.encode('utf-8'),
                        file_name=SUBMISSION_FILENAME,
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    st.error(f"**Submission Validation Failed:** {error_msg}")
                    st.button("⬇ Download Submission CSV", disabled=True, use_container_width=True)
