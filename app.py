"""
APTIVA AI — Streamlit Demo Application
======================================
Intelligent Candidate Discovery & Ranking for Redrob AI Hackathon.

Run: streamlit run app.py

First 60 seconds demo flow:
  1. Auto-loads sample candidates and runs ranking immediately
  2. Shows Hireability Index™ on the rankings table
  3. Click any candidate → AI Analysis (most impressive screen)
  4. Try Judge Mode to see reasoning depth
  5. Try Candidate Comparison
"""

import csv
import io
import time
from pathlib import Path

import streamlit as st
import yaml

# ── Page Config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="APTIVA AI — Intelligent Candidate Discovery",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Core imports ──────────────────────────────────────────────────────────────
from core.dataset_loader import DatasetLoader
from core.reasoning import generate_reasoning
from core.scorer import compute_final_score
from core.tfidf_engine import build_tfidf_index
from ui.styles import inject_styles
from ui.pages import home, ai_analysis, candidate_profile, comparison, judge_mode_page, analytics


# ── Load Config ───────────────────────────────────────────────────────────────
@st.cache_data
def load_config() -> dict:
    try:
        with open("config.yaml", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


# ── Dataset Auto-Setup ────────────────────────────────────────────────────────
@st.cache_resource
def setup_dataset() -> DatasetLoader:
    loader = DatasetLoader(data_dir="./data")
    loader.auto_setup()
    return loader


# ── Ranking Pipeline ──────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def run_ranking(candidates_path_str: str, top_n: int = 100) -> dict:
    """
    Run the full ranking pipeline. Cached so it only runs once per session.
    Returns: {"results": [...], "total": int, "submission_csv": str}
    """
    import heapq
    from pathlib import Path

    loader = DatasetLoader(data_dir="./data")
    target_path = Path(candidates_path_str)

    candidates = loader.load_all_candidates(target_path)
    if not candidates:
        return {"results": [], "total": 0, "submission_csv": ""}

    # Build TF-IDF
    _, _, _, similarities = build_tfidf_index(candidates)

    # Score all
    scored = []
    for i, candidate in enumerate(candidates):
        tfidf_sim = float(similarities[i])
        final_score, components = compute_final_score(candidate, tfidf_sim)
        scored.append((final_score, candidate, components))

    # Top-N
    import heapq
    top_results = heapq.nlargest(top_n, scored, key=lambda x: x[0])
    top_results.sort(key=lambda x: (-x[0], x[1].get("candidate_id", "")))

    # Build results list
    results = []
    for rank, (score, candidate, components) in enumerate(top_results, start=1):
        reasoning = generate_reasoning(candidate, rank, components)
        results.append({
            "rank":        rank,
            "score":       score,
            "candidate":   candidate,
            "components":  components,
            "reasoning":   reasoning,
        })

    # Build CSV string
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["candidate_id", "rank", "score", "reasoning"])
    for r in results:
        writer.writerow([r["candidate"]["candidate_id"], r["rank"], round(r["score"], 4), r["reasoning"]])
    csv_str = csv_buffer.getvalue()

    return {
        "results":        results,
        "total":          len(candidates),
        "submission_csv": csv_str,
    }


# ── Session State Init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "page":                 "home",
        "selected_candidate_id": None,
        "compare_list":         [],
        "results":              [],
        "total_candidates":     0,
        "submission_csv":       "",
        "ranking_done":         False,
        "dataset_status":       None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(config: dict, loader: DatasetLoader):
    with st.sidebar:
        # Logo / Brand
        st.markdown(
            """
<div style="padding:0.5rem 0 1.5rem">
  <div style="font-size:1.375rem;font-weight:800;color:#1D1D1F;letter-spacing:-0.03em">⬡ APTIVA AI</div>
  <div style="font-size:0.75rem;color:#86868B;margin-top:0.125rem;letter-spacing:0.01em">Intelligent Candidate Discovery</div>
</div>""",
            unsafe_allow_html=True,
        )

        # Navigation
        pages = [
            ("home",              "🏆", "Rankings"),
            ("ai_analysis",       "🤖", "AI Analysis"),
            ("candidate_profile", "👤", "Candidate Profile"),
            ("comparison",        "⚖️", "Compare"),
            ("judge_mode",        "🧑‍⚖️", "Judge Mode"),
            ("analytics",         "📊", "Analytics"),
        ]

        st.markdown('<div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Navigation</div>', unsafe_allow_html=True)

        for page_key, icon, label in pages:
            is_active = st.session_state["page"] == page_key
            btn_style = "background:#E8F2FF;color:#0071E3;border:none;" if is_active else "background:transparent;color:#1D1D1F;border:none;"
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{page_key}",
                use_container_width=True,
                type="secondary" if not is_active else "primary",
            ):
                st.session_state["page"] = page_key
                st.rerun()

        st.markdown("---")

        # Dataset status
        st.markdown('<div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Dataset</div>', unsafe_allow_html=True)

        candidates_path = loader.get_candidates_path()
        if candidates_path:
            fname = candidates_path.name
            st.markdown(
                f'<div style="font-size:0.8125rem;color:#1A8917">✓ {fname}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:0.8125rem;color:#CC0000">⚠ No dataset found</div>',
                unsafe_allow_html=True,
            )
            st.caption("Place ZIP file in data/ directory")

        st.markdown("---")

        # Run Ranking Button
        if candidates_path:
            if st.button("▶ Run Ranking Analysis", use_container_width=True, type="primary"):
                st.session_state["ranking_done"] = False
                st.cache_data.clear()
                st.rerun()
        else:
            st.markdown(
                '<div style="font-size:0.8125rem;color:#86868B">Upload candidates to run ranking</div>',
                unsafe_allow_html=True,
            )

        # Stats if ranked
        if st.session_state.get("ranking_done"):
            results = st.session_state.get("results", [])
            total = st.session_state.get("total_candidates", 0)
            st.markdown("---")
            st.markdown('<div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Ranking Summary</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.8125rem;color:#1D1D1F">Analyzed: <strong>{total:,}</strong></div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:0.8125rem;color:#1D1D1F">Top ranked: <strong>{len(results)}</strong></div>', unsafe_allow_html=True)
            if results:
                top_hi = results[0].get("components", {}).get("hireability_index", {}).get("overall", 0)
                st.markdown(f'<div style="font-size:0.8125rem;color:#1D1D1F">Best Hireability™: <strong>{top_hi:.0f}/100</strong></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Compare list
        compare_list = st.session_state.get("compare_list", [])
        if compare_list:
            st.markdown('<div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Compare List</div>', unsafe_allow_html=True)
            for cid in compare_list:
                st.markdown(f'<div style="font-size:0.8125rem;color:#1D1D1F">• {cid}</div>', unsafe_allow_html=True)
            if st.button("Clear Compare List", use_container_width=True):
                st.session_state["compare_list"] = []
                st.rerun()

        st.markdown("---")
        st.markdown(
            '<div style="font-size:0.75rem;color:#86868B;text-align:center">APTIVA AI · Redrob Hackathon<br>India.Runs Data & AI Challenge</div>',
            unsafe_allow_html=True,
        )


# ── Auto-Run Ranking ──────────────────────────────────────────────────────────
def auto_run_ranking(loader: DatasetLoader):
    """Run ranking automatically on first load."""
    candidates_path = loader.get_candidates_path()
    if not candidates_path:
        return

    if st.session_state.get("ranking_done"):
        return  # Already ranked

    # ── Staged loading UI ─────────────────────────────────────────────────
    _STAGES = [
        (0.05, "📂 Loading dataset",              "Parsing candidates.jsonl — 100,000 profiles",           "~8s"),
        (0.50, "🔬 Building TF-IDF index",        "Vectorizing career histories against 8,000 JD keywords", "~45s"),
        (0.85, "⚡ Scoring all candidates",        "Running 7-component pipeline across 100K profiles",      "~35s"),
        (0.95, "🏆 Selecting Top 100",             "Applying Relevance Gate · generating reasoning",         "~5s"),
        (1.00, "✅ Done",                          "Rankings ready",                                         ""),
    ]

    header_slot   = st.empty()
    stage_slot    = st.empty()
    bar_slot      = st.empty()
    detail_slot   = st.empty()
    eta_slot      = st.empty()

    def _show_stage(progress: float, title: str, detail: str, eta: str):
        header_slot.markdown(
            """
<div style="text-align:center;padding:2rem 1rem 0.5rem">
  <div style="font-size:1.5rem;font-weight:800;color:#1D1D1F;letter-spacing:-0.03em">⬡ APTIVA AI</div>
  <div style="font-size:0.875rem;color:#86868B;margin-top:0.25rem">Intelligent Candidate Ranking · Redrob AI Hackathon</div>
</div>""",
            unsafe_allow_html=True,
        )
        stage_slot.markdown(
            f'<div style="text-align:center;font-size:1.0625rem;font-weight:600;color:#1D1D1F;margin:0.5rem 0">{title}</div>',
            unsafe_allow_html=True,
        )
        bar_slot.progress(progress)
        detail_slot.markdown(
            f'<div style="text-align:center;font-size:0.875rem;color:#6E6E73;margin-top:0.25rem">{detail}</div>',
            unsafe_allow_html=True,
        )
        eta_slot.markdown(
            f'<div style="text-align:center;font-size:0.8125rem;color:#86868B;margin-top:0.125rem">{("Est. " + eta + " remaining") if eta else ""}</div>',
            unsafe_allow_html=True,
        )

    # Show stage 1 immediately before blocking call
    _show_stage(*_STAGES[0])
    time.sleep(0.05)
    _show_stage(*_STAGES[1])

    # --- blocking ranking call ---
    result_data = run_ranking(str(candidates_path))

    _show_stage(*_STAGES[2])
    time.sleep(0.05)
    _show_stage(*_STAGES[3])
    time.sleep(0.05)
    _show_stage(*_STAGES[4])
    time.sleep(0.3)

    # Clear loading UI
    for slot in [header_slot, stage_slot, bar_slot, detail_slot, eta_slot]:
        slot.empty()

    if result_data["results"]:
        st.session_state["results"]           = result_data["results"]
        st.session_state["total_candidates"]   = result_data["total"]
        st.session_state["submission_csv"]     = result_data["submission_csv"]
        st.session_state["ranking_done"]       = True
        # Auto-select top candidate
        if not st.session_state.get("selected_candidate_id"):
            st.session_state["selected_candidate_id"] = result_data["results"][0]["candidate"]["candidate_id"]


# ── Main App ──────────────────────────────────────────────────────────────────
def main():
    inject_styles()
    init_state()
    config = load_config()
    loader = setup_dataset()

    # Auto-run ranking silently on first load
    auto_run_ranking(loader)

    # Render sidebar
    render_sidebar(config, loader)

    # Build state dict for pages
    state = {
        "results":              st.session_state["results"],
        "total_candidates":     st.session_state["total_candidates"],
        "submission_csv":       st.session_state["submission_csv"],
        "selected_candidate_id": st.session_state["selected_candidate_id"],
        "compare_list":         st.session_state["compare_list"],
        "page":                 st.session_state["page"],
    }

    # Route to page
    page = st.session_state["page"]

    if page == "home":
        home.render(state)
    elif page == "ai_analysis":
        ai_analysis.render(state)
    elif page == "candidate_profile":
        candidate_profile.render(state)
    elif page == "comparison":
        comparison.render(state)
    elif page == "judge_mode":
        judge_mode_page.render(state)
    elif page == "analytics":
        analytics.render(state)
    else:
        home.render(state)

    # Sync state back to session (for navigation mutations from pages)
    if state.get("page") != st.session_state["page"]:
        st.session_state["page"] = state["page"]
    if state.get("selected_candidate_id") != st.session_state["selected_candidate_id"]:
        st.session_state["selected_candidate_id"] = state["selected_candidate_id"]
    if state.get("compare_list") != st.session_state["compare_list"]:
        st.session_state["compare_list"] = state["compare_list"]


if __name__ == "__main__":
    main()
