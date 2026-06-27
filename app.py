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
    page_icon="🔷",
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
        "page":                  "home",
        "selected_candidate_id": None,
        "compare_list":          [],
        "results":               [],
        "total_candidates":      0,
        "submission_csv":        "",
        "ranking_done":          False,
        "ranking_running":       False,
        "ranking_error":         None,
        "dataset_status":        None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(config: dict, loader: DatasetLoader):
    with st.sidebar:
        # Logo / Brand
        _logo_hex = '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-3px"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/></svg>'
        st.markdown(
            f"""
<div style="padding:0.5rem 0 1.5rem">
  <div style="font-size:1.375rem;font-weight:800;color:#1D1D1F;letter-spacing:-0.03em;display:flex;align-items:center;gap:0.4rem">{_logo_hex} APTIVA AI</div>
  <div style="font-size:0.75rem;color:#86868B;margin-top:0.125rem;letter-spacing:0.01em">Intelligent Candidate Discovery</div>
</div>""",
            unsafe_allow_html=True,
        )

        # Navigation
        # SVG icons — Lucide-style, 16×16, stroke-based
        _ICONS = {
            "home": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
            "ai_analysis": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
            "candidate_profile": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
            "comparison": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
            "judge_mode": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
            "analytics": '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="18" y="3" width="4" height="18"/><rect x="10" y="8" width="4" height="13"/><rect x="2" y="13" width="4" height="8"/></svg>',
        }

        pages = [
            ("home",              "Rankings"),
            ("ai_analysis",       "AI Analysis"),
            ("candidate_profile", "Candidate Profile"),
            ("comparison",        "Compare"),
            ("judge_mode",        "Judge Mode"),
            ("analytics",         "Analytics"),
        ]

        st.markdown('<div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Navigation</div>', unsafe_allow_html=True)

        for page_key, label in pages:
            is_active = st.session_state["page"] == page_key
            icon_svg = _ICONS.get(page_key, "")
            active_style = (
                "background:#E8F2FF;color:#0071E3;border:1px solid #C8DEFF;"
                if is_active else
                "background:transparent;color:#1D1D1F;border:1px solid transparent;"
            )
            # Render as an HTML nav item so the SVG icon shows cleanly
            st.markdown(
                f'<div style="{active_style}display:flex;align-items:center;gap:0.625rem;'
                f'padding:0.5rem 0.75rem;border-radius:6px;margin:0.125rem 0;'
                f'font-size:0.875rem;font-weight:500;cursor:pointer">'
                f'{icon_svg}<span>{label}</span></div>',
                unsafe_allow_html=True,
            )
            # Invisible button that captures the click
            if st.button(label, key=f"nav_{page_key}", use_container_width=True,
                         type="secondary" if not is_active else "primary"):
                st.session_state["page"] = page_key
                st.rerun()

        st.markdown("---")

        # Dataset status
        st.markdown('<div style="font-size:0.6875rem;font-weight:600;color:#86868B;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">Dataset</div>', unsafe_allow_html=True)

        candidates_path = loader.get_candidates_path()
        if candidates_path:
            fname = candidates_path.name
            _ck = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#1A8917" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-1px"><polyline points="20 6 9 17 4 12"/></svg>'
            st.markdown(
                f'<div style="font-size:0.8125rem;color:#1A8917;display:flex;align-items:center;gap:0.35rem">{_ck} {fname}</div>',
                unsafe_allow_html=True,
            )
        else:
            _warn = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#CC0000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-1px"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
            st.markdown(
                f'<div style="font-size:0.8125rem;color:#CC0000;display:flex;align-items:center;gap:0.35rem">{_warn} No dataset found</div>',
                unsafe_allow_html=True,
            )
            st.caption("Place ZIP file in data/ directory")

        st.markdown("---")

        # Run Ranking Button
        if candidates_path:
            if st.session_state.get("ranking_running"):
                # Disabled state shown while analysis is running
                _ldr = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#86868B" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-1px"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>'
                st.markdown(
                    f'<div style="background:#F5F5F7;border-radius:6px;padding:0.5rem 0.75rem;'
                    f'font-size:0.8125rem;color:#86868B;text-align:center;cursor:not-allowed;'
                    f'display:flex;align-items:center;justify-content:center;gap:0.4rem">'
                    f'{_ldr} Running Analysis…</div>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button("▶ Run Ranking Analysis", use_container_width=True, type="primary"):
                    st.session_state["ranking_done"]    = False
                    st.session_state["ranking_error"]   = None
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

    # ── Premium Loading Screen ────────────────────────────────────────────
    # All UI lives in a single HTML slot so updates feel like transitions,
    # not Streamlit widget flashes. Only the slot content is swapped.
    loading_slot = st.empty()

    _CSS = """
<style>
@keyframes aptiva-fadein {
  from { opacity:0; }
  to   { opacity:1; }
}
@keyframes aptiva-fadeout {
  from { opacity:1; }
  to   { opacity:0; }
}
@keyframes aptiva-label-pulse {
  0%,100% { opacity:1; }
  50%      { opacity:0.6; }
}
.aptiva-exiting {
  animation: aptiva-fadeout 0.4s ease forwards !important;
  pointer-events: none !important;
}
.aptiva-loader {
  /* True full-screen: covers sidebar, main area, and everything else */
  position: fixed; top: 0; left: 0;
  width: 100vw; height: 100vh;
  z-index: 9999999;
  background: #FFFFFF;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  animation: aptiva-fadein 0.3s ease;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  /* Capture all pointer events so nothing behind can be clicked */
  pointer-events: all;
  cursor: wait;
  /* Scroll lock via overflow */
  overflow: hidden;
}
.aptiva-logo {
  font-size:1.625rem; font-weight:800; color:#1D1D1F;
  letter-spacing:-0.035em; margin-bottom:0.375rem;
}
.aptiva-sub {
  font-size:0.8125rem; color:#86868B; letter-spacing:0.02em;
  margin-bottom:2.5rem;
}
/* Progress bar */
.aptiva-bar-track {
  width:min(480px,90vw); height:3px;
  background:#E5E5EA; border-radius:2px;
  overflow:hidden; margin-bottom:2rem;
}
.aptiva-bar-fill {
  height:100%; background:#0071E3;
  border-radius:2px;
  transition:width 0.8s cubic-bezier(0.4,0,0.2,1);
}
/* Pipeline list */
.aptiva-pipeline {
  width:min(400px,88vw); margin-bottom:1.5rem;
}
.aptiva-step {
  display:flex; align-items:baseline; gap:0.75rem;
  padding:0.3rem 0; font-size:0.875rem;
}
.aptiva-step-icon {
  width:1.125rem; text-align:center; flex-shrink:0;
  font-size:0.875rem; font-weight:600; line-height:1.4;
}
.aptiva-step-done  { color:#1A8917; }
.aptiva-step-active { color:#0071E3; }
.aptiva-step-idle  { color:#C7C7CC; }
.aptiva-step-label-done   { color:#1D1D1F; }
.aptiva-step-label-active {
  color:#0071E3; font-weight:600;
  animation:aptiva-label-pulse 2s ease-in-out infinite;
}
.aptiva-step-label-idle   { color:#C7C7CC; }
/* Active stage detail */
.aptiva-detail {
  font-size:0.8125rem; color:#6E6E73;
  text-align:center; min-height:1.25rem;
  margin-bottom:2rem; max-width:400px;
}
/* Stats grid */
.aptiva-stats {
  display:grid; grid-template-columns:repeat(5,1fr);
  gap:0.75rem; width:min(520px,92vw); margin-bottom:2rem;
}
.aptiva-stat {
  display:flex; flex-direction:column; align-items:center;
  background:#F5F5F7; border-radius:8px; padding:0.625rem 0.375rem;
}
.aptiva-stat-val {
  font-size:0.9375rem; font-weight:700; color:#1D1D1F;
  letter-spacing:-0.02em; line-height:1.2;
}
.aptiva-stat-label {
  font-size:0.625rem; color:#86868B; text-align:center;
  text-transform:uppercase; letter-spacing:0.07em;
  margin-top:0.25rem; line-height:1.3;
}
/* ETA block */
.aptiva-eta {
  text-align:center; margin-bottom:1.75rem; min-height:3.5rem;
}
.aptiva-eta-label {
  font-size:0.6875rem; color:#86868B; text-transform:uppercase;
  letter-spacing:0.1em; margin-bottom:0.25rem;
}
.aptiva-eta-value {
  font-size:1.5rem; font-weight:700; color:#1D1D1F;
  letter-spacing:-0.03em;
}
/* Footer */
.aptiva-footer {
  font-size:0.6875rem; color:#C7C7CC; text-align:center;
  letter-spacing:0.03em; padding-top:0.5rem;
  border-top:1px solid #F0F0F5; width:min(480px,90vw);
}
</style>
"""

    _PIPELINE = [
        ("Load Dataset",                  "Reading and validating 100,000 candidate profiles."),
        ("Build TF-IDF Index",            "Creating an 8,000-feature career similarity index."),
        ("Score Candidates",              "Running the 7-component ranking engine across all profiles."),
        ("Generate Ranking Explanations", "Creating transparent, fact-grounded ranking explanations."),
        ("Select Top 100",                "Selecting the highest-ranked AI/ML candidates by Final Score."),
    ]

    # stage_idx = which step is currently active (0-based).
    def _render(stage_idx: int, progress: float, eta: str, complete: bool = False):
        steps_html = ""
        for i, (label, _) in enumerate(_PIPELINE):
            if complete or i < stage_idx:
                icon_cls = "aptiva-step-done"
                lbl_cls  = "aptiva-step-label-done"
                # SVG check mark
                icon_ch  = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
            elif i == stage_idx:
                icon_cls = "aptiva-step-active"
                lbl_cls  = "aptiva-step-label-active"
                # SVG right-pointing triangle (play)
                icon_ch  = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="5 3 19 12 5 21 5 3"/></svg>'
            else:
                icon_cls = "aptiva-step-idle"
                lbl_cls  = "aptiva-step-label-idle"
                # Small circle (pending)
                icon_ch  = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="8"/></svg>'
            steps_html += (
                f'<div class="aptiva-step">'
                f'<span class="aptiva-step-icon {icon_cls}">{icon_ch}</span>'
                f'<span class="{lbl_cls}">{label}</span>'
                f'</div>'
            )

        if complete:
            detail = ""
        elif 0 <= stage_idx < len(_PIPELINE):
            detail = _PIPELINE[stage_idx][1]
        else:
            detail = ""

        bar_pct = min(100, int(progress * 100))

        if complete:
            _ck_green = '<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#1A8917" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
            eta_block = (
                f'<div class="aptiva-eta-label" style="color:#1A8917;letter-spacing:0.06em;display:flex;align-items:center;gap:0.3rem">'
                f'{_ck_green} Initialization Complete</div>'
                f'<div class="aptiva-eta-value" style="color:#1A8917;font-size:1.0625rem;font-weight:600">'
                f'Launching APTIVA AI…</div>'
            )
        elif eta:
            eta_block = (
                f'<div class="aptiva-eta-label">Estimated Remaining Time</div>'
                f'<div class="aptiva-eta-value">{eta}</div>'
            )
        else:
            eta_block = f'<div class="aptiva-eta-label">&nbsp;</div><div class="aptiva-eta-value">&nbsp;</div>'

        # Inject scroll lock JS in every frame (persists on DOM as long as overlay is visible)
        scroll_lock_js = """
<script>
(function(){
  document.documentElement.style.overflow='hidden';
  document.body.style.overflow='hidden';
  // Also lock Streamlit's own scroll container
  var main=document.querySelector('[data-testid="stAppViewContainer"]');
  if(main) main.style.overflow='hidden';
})();
</script>"""

        html = f"""{_CSS}
{scroll_lock_js}
<div class="aptiva-loader" id="aptiva-overlay">
  <div class="aptiva-logo"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-4px;margin-right:0.3rem"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/></svg> APTIVA AI</div>
  <div class="aptiva-sub">Intelligent Candidate Ranking &middot; Redrob AI Hackathon</div>

  <div class="aptiva-bar-track">
    <div class="aptiva-bar-fill" style="width:{bar_pct}%"></div>
  </div>

  <div class="aptiva-pipeline">{steps_html}</div>

  <div class="aptiva-detail">{detail}</div>

  <div class="aptiva-stats">
    <div class="aptiva-stat">
      <div class="aptiva-stat-val">100,000</div>
      <div class="aptiva-stat-label">Dataset<br>Candidates</div>
    </div>
    <div class="aptiva-stat">
      <div class="aptiva-stat-val">7</div>
      <div class="aptiva-stat-label">Ranking Engine<br>Components</div>
    </div>
    <div class="aptiva-stat">
      <div class="aptiva-stat-val">8,000</div>
      <div class="aptiva-stat-label">Career Index<br>Features</div>
    </div>
    <div class="aptiva-stat">
      <div class="aptiva-stat-val">CPU Only</div>
      <div class="aptiva-stat-label">Execution<br>Mode</div>
    </div>
    <div class="aptiva-stat">
      <div class="aptiva-stat-val">&lt;5 min</div>
      <div class="aptiva-stat-label">Target<br>Runtime</div>
    </div>
  </div>

  <div class="aptiva-eta">{eta_block}</div>

  <div class="aptiva-footer">
    Deterministic Ranking &bull; Explainable AI &bull; CPU Only &bull; Fully Reproducible
  </div>
</div>"""
        loading_slot.markdown(html, unsafe_allow_html=True)

    # ── Mark as running (disables sidebar button) ─────────────────────────
    st.session_state["ranking_running"] = True

    # Stage 0 — dataset loading (renders before blocking call)
    _render(0, 0.05, "~90 seconds")
    time.sleep(0.08)
    # Stage 1 — TF-IDF indexing (bulk of wall-clock time)
    _render(1, 0.10, "~80 seconds")

    # ── blocking ranking call ─────────────────────────────────────────────
    result_data = None
    try:
        result_data = run_ranking(str(candidates_path))
    except Exception as exc:
        # ── Error state: show clean failure overlay ───────────────────────
        error_html = f"""{_CSS}
<script>
document.documentElement.style.overflow='hidden';
document.body.style.overflow='hidden';
</script>
<div class="aptiva-loader" id="aptiva-overlay">
  <div class="aptiva-logo">&#x2B21; APTIVA AI</div>
  <div class="aptiva-sub">Intelligent Candidate Ranking &middot; Redrob AI Hackathon</div>
  <div style="margin:2rem 0;text-align:center">
    <div style="font-size:2rem;margin-bottom:0.75rem">&#9888;</div>
    <div style="font-size:1rem;font-weight:600;color:#CC0000;margin-bottom:0.5rem">Initialization Failed</div>
    <div style="font-size:0.8125rem;color:#6E6E73;max-width:360px">{exc}</div>
  </div>
  <div style="margin-top:1rem;font-size:0.8125rem;color:#86868B;text-align:center">
    Click <strong>&#9654; Run Ranking Analysis</strong> in the sidebar to retry.
  </div>
  <div class="aptiva-footer" style="margin-top:2rem">
    Deterministic Ranking &bull; Explainable AI &bull; CPU Only &bull; Fully Reproducible
  </div>
</div>"""
        loading_slot.markdown(error_html, unsafe_allow_html=True)
        time.sleep(3.0)   # Show error for 3 s, then unlock UI
        # Unlock scroll before clearing
        loading_slot.markdown(
            '<script>document.documentElement.style.overflow="";'
            'document.body.style.overflow="";</script>',
            unsafe_allow_html=True,
        )
        time.sleep(0.1)
        loading_slot.empty()
        st.session_state["ranking_running"] = False
        st.session_state["ranking_error"]   = str(exc)
        return
    # ─────────────────────────────────────────────────────────────────────

    # Smooth sweep through remaining stages with interpolated progress.
    _render(2, 0.80, "~4 seconds");  time.sleep(0.12)
    _render(2, 0.85, "~3 seconds");  time.sleep(0.12)
    _render(3, 0.88, "~2 seconds");  time.sleep(0.12)
    _render(3, 0.92, "~1 second");   time.sleep(0.12)
    _render(4, 0.95, "~1 second");   time.sleep(0.12)
    _render(4, 0.98, "<1 second");   time.sleep(0.12)

    # Completion state -- shows check mark + Initialization Complete / Launching APTIVA AI
    _render(4, 1.00, "", complete=True)
    time.sleep(0.75)   # 700-800 ms dwell before clearing (per spec)

    # Fade-out: switch to aptiva-exiting class + unlock scroll simultaneously
    fadeout_html = f"""{_CSS}
<script>
document.documentElement.style.overflow='';
document.body.style.overflow='';
var main=document.querySelector('[data-testid="stAppViewContainer"]');
if(main) main.style.overflow='';
</script>
<div class="aptiva-loader aptiva-exiting" id="aptiva-overlay">
  <div class="aptiva-logo"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-4px;margin-right:0.3rem"><polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/></svg> APTIVA AI</div>
  <div class="aptiva-sub">Intelligent Candidate Ranking &middot; Redrob AI Hackathon</div>
  <div class="aptiva-bar-track"><div class="aptiva-bar-fill" style="width:100%"></div></div>
  <div style="text-align:center;margin-top:2rem">
    <div style="font-size:0.6875rem;color:#1A8917;text-transform:uppercase;letter-spacing:0.06em;display:flex;align-items:center;justify-content:center;gap:0.3rem">
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#1A8917" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg> Initialization Complete</div>
    <div style="font-size:1.0625rem;font-weight:600;color:#1A8917;margin-top:0.25rem">
      Launching APTIVA AI&hellip;</div>
  </div>
</div>"""
    loading_slot.markdown(fadeout_html, unsafe_allow_html=True)
    time.sleep(0.45)   # Match aptiva-fadeout animation duration (0.4s)
    loading_slot.empty()

    # ── Commit results to session state ───────────────────────────────────
    st.session_state["ranking_running"] = False
    if result_data and result_data["results"]:
        st.session_state["results"]           = result_data["results"]
        st.session_state["total_candidates"]  = result_data["total"]
        st.session_state["submission_csv"]    = result_data["submission_csv"]
        st.session_state["ranking_done"]      = True
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

    # Pass session state directly — pages read/write the live store.
    # (A copy dict would silently discard writes, breaking navigation context.)
    state = st.session_state

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
