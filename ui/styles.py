"""
APTIVA AI — Apple-Inspired Design System
CSS injection for Streamlit. Clean, minimal, enterprise-grade.
Fonts: -apple-system / SF Pro Display. No glassmorphism. No neon.
"""

import streamlit as st


def inject_styles():
    """Inject all global CSS styles into the Streamlit app."""
    st.markdown(
        """
<style>
/* ── Fonts ─────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Root Variables ─────────────────────────────────────────────────────── */
:root {
  --bg:           #FFFFFF;
  --surface:      #F5F5F7;
  --surface-2:    #EBEBED;
  --border:       #D2D2D7;
  --border-light: #E8E8ED;
  --text:         #1D1D1F;
  --text-2:       #6E6E73;
  --text-3:       #86868B;
  --accent:       #0071E3;
  --accent-hover: #0077ED;
  --accent-light: #E8F2FF;
  --success:      #1A8917;
  --success-bg:   #EBF5EA;
  --warning:      #C47000;
  --warning-bg:   #FFF3E0;
  --danger:       #CC0000;
  --danger-bg:    #FFEBEB;
  --shadow-sm:    0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md:    0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
  --radius:       10px;
  --radius-sm:    6px;
  --radius-lg:    14px;
  --font:         -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Helvetica Neue", sans-serif;
}

/* ── Force Light Mode Everything ─────────────────────────────────────────── */
html, body,
.stApp, .stApp > div,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > section,
[data-testid="stMain"],
.main,
.block-container {
  background-color: #FFFFFF !important;
  color: #1D1D1F !important;
}

/* ── Global Font Override ─────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Inter", "Helvetica Neue", sans-serif !important;
}

/* ── Hide Streamlit Branding ─────────────────────────────────────────── */
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: #F5F5F7 !important;
  border-right: 1px solid #E8E8ED !important;
}
[data-testid="stSidebar"] > div {
  background-color: #F5F5F7 !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 1.5rem 1rem;
  background-color: #F5F5F7 !important;
}
[data-testid="stSidebar"] * {
  color: #1D1D1F !important;
}

/* ── Hide Sidebar Collapse Controls ────────────────────────────────────── */
[data-testid="stSidebarCollapseButton"] {
  display: none !important;
}

[data-testid="collapsedControl"] {
  display: none !important;
}


/* ── Main Content Area ───────────────────────────────────────────────── */
.main .block-container {
  padding: 1.5rem 2rem 3rem 2rem;
  max-width: 1400px;
  background-color: #FFFFFF !important;
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
  background-color: #F5F5F7 !important;
  border-right: 1px solid #E8E8ED !important;
}
[data-testid="stSidebar"] > div {
  background-color: #F5F5F7 !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 1.5rem 1rem;
  background-color: #F5F5F7 !important;
}
[data-testid="stSidebar"] * {
  color: #1D1D1F !important;
}

/* ── Typography ───────────────────────────────────────────────────────── */
h1 { font-size: 1.875rem !important; font-weight: 700 !important; letter-spacing: -0.025em !important; color: #1D1D1F !important; }
h2 { font-size: 1.375rem !important; font-weight: 600 !important; letter-spacing: -0.015em !important; color: #1D1D1F !important; }
h3 { font-size: 1.125rem !important; font-weight: 600 !important; color: #1D1D1F !important; }
p  { font-size: 0.9375rem !important; line-height: 1.6 !important; color: #6E6E73 !important; }
label, .stMarkdown, .stText { color: #1D1D1F !important; }

/* ── Metric Cards ────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: #F5F5F7 !important;
  border: 1px solid #E8E8ED !important;
  border-radius: 10px !important;
  padding: 1rem 1.25rem !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.625rem !important;
  font-weight: 700 !important;
  color: #1D1D1F !important;
}
[data-testid="stMetricLabel"] {
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  color: #86868B !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}
[data-testid="stMetricDelta"] {
  font-size: 0.75rem !important;
  color: #6E6E73 !important;
}

/* ── ALL Buttons — Primary Style ─────────────────────────────────────── */
.stButton > button {
  background-color: #0071E3 !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 6px !important;
  font-size: 0.875rem !important;
  font-weight: 600 !important;
  padding: 0.5rem 1rem !important;
  letter-spacing: -0.01em !important;
  transition: background-color 0.15s ease !important;
  width: 100% !important;
}
.stButton > button:hover {
  background-color: #0077ED !important;
  color: #FFFFFF !important;
}
.stButton > button:active {
  background-color: #006ACD !important;
  color: #FFFFFF !important;
}
.stButton > button p,
.stButton > button span,
.stButton > button div {
  color: #FFFFFF !important;
  font-weight: 600 !important;
}

/* ── Secondary / ghost buttons ──────────────────────────────────────── */
.stButton > button[kind="secondary"] {
  background-color: #F5F5F7 !important;
  color: #0071E3 !important;
  border: 1px solid #D2D2D7 !important;
}
.stButton > button[kind="secondary"]:hover {
  background-color: #E8F2FF !important;
  color: #0071E3 !important;
}
.stButton > button[kind="secondary"] p,
.stButton > button[kind="secondary"] span {
  color: #0071E3 !important;
}

/* ── Download button ────────────────────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
  background-color: #F5F5F7 !important;
  color: #0071E3 !important;
  border: 1px solid #D2D2D7 !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
}

/* ── Sidebar nav: overlay buttons are invisible — HTML items do the visual */
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
  opacity: 0 !important;
  height: 0 !important;
  min-height: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  border: none !important;
  pointer-events: all !important; /* still captures clicks */
  position: relative !important;
  z-index: 1 !important;
}
/* The visible HTML nav row is above; the invisible button sits behind it */
[data-testid="stSidebar"] .stButton {
  margin-top: -2.375rem !important; /* pull button up to overlap the HTML row */
  margin-bottom: 0 !important;
}

/* ── Inputs / Selects ────────────────────────────────────────────────── */
.stSelectbox > div > div,
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
  background-color: #FFFFFF !important;
  color: #1D1D1F !important;
  border: 1px solid #D2D2D7 !important;
  border-radius: 6px !important;
}
.stSelectbox [data-baseweb="select"] {
  background-color: #FFFFFF !important;
  border-color: #D2D2D7 !important;
}
.stSelectbox [data-baseweb="select"] > div {
  background-color: #FFFFFF !important;
  color: #1D1D1F !important;
}

/* ── Slider ──────────────────────────────────────────────────────────── */
.stSlider [data-baseweb="slider"] [role="slider"] {
  background-color: #0071E3 !important;
  border-color: #0071E3 !important;
}

/* ── Multiselect ─────────────────────────────────────────────────────── */
.stMultiSelect [data-baseweb="select"] {
  background-color: #FFFFFF !important;
  border-color: #D2D2D7 !important;
}
[data-baseweb="tag"] {
  background-color: #E8F2FF !important;
  color: #0071E3 !important;
}

/* ── Tabs ─────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0 !important;
  border-bottom: 1px solid #E8E8ED !important;
  background-color: transparent !important;
}
.stTabs [data-baseweb="tab"] {
  padding: 0.625rem 1.25rem !important;
  font-size: 0.875rem !important;
  font-weight: 500 !important;
  color: #6E6E73 !important;
  background: transparent !important;
  border: none !important;
  border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
  color: #0071E3 !important;
  border-bottom-color: #0071E3 !important;
  background: transparent !important;
}
[data-testid="stTabsContent"] {
  background-color: #FFFFFF !important;
}

/* ── Progress Bar ────────────────────────────────────────────────────── */
.stProgress > div > div {
  background-color: #0071E3 !important;
  border-radius: 4px;
}

/* ── Divider ─────────────────────────────────────────────────────────── */
hr { border: none !important; border-top: 1px solid #E8E8ED !important; margin: 1.5rem 0 !important; }

/* ── Custom Component Classes ────────────────────────────────────────── */

/* Card */
.aptiva-card {
  background: #FFFFFF !important;
  border: 1px solid #E8E8ED !important;
  border-radius: 10px !important;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04) !important;
  margin-bottom: 1rem;
}

/* Score Badge */
.score-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8125rem;
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  letter-spacing: 0.01em;
}
.badge-strong-yes { background: #EBF5EA; color: #1A8917; }
.badge-yes        { background: #E3F2FD; color: #1565C0; }
.badge-maybe      { background: #FFF3E0; color: #C47000; }
.badge-no         { background: #FFEBEB; color: #CC0000; }

/* Hireability Index Score Ring */
.hi-score-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
}
.hi-score {
  font-size: 3rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: #1D1D1F;
  line-height: 1;
}
.hi-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #86868B;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Component Score Bar */
.score-bar-container { margin: 0.5rem 0; }
.score-bar-label {
  display: flex;
  justify-content: space-between;
  font-size: 0.8125rem;
  color: #6E6E73;
  margin-bottom: 0.25rem;
}
.score-bar-track {
  height: 4px;
  background: #EBEBED;
  border-radius: 4px;
  overflow: hidden;
}
.score-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
  background: #0071E3;
}

/* Stat Row */
.stat-row {
  display: flex;
  gap: 1rem;
  margin: 0.75rem 0;
}
.stat-item {
  flex: 1;
  background: #F5F5F7;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  text-align: center;
}
.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1D1D1F;
}
.stat-label {
  font-size: 0.75rem;
  color: #86868B;
  margin-top: 0.125rem;
}

/* Tag / Chip */
.skill-tag {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  margin: 0.125rem;
}
.skill-tag-present { background: #EBF5EA; color: #1A8917; }
.skill-tag-missing  { background: #FFEBEB; color: #CC0000; }
.skill-tag-bonus    { background: #EDE7F6; color: #5E35B1; }
.skill-tag-neutral  { background: #EBEBED;  color: #6E6E73; }

/* Section Header */
.section-header {
  font-size: 0.6875rem;
  font-weight: 600;
  color: #86868B;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #E8E8ED;
}

/* Judge Mode Verdict */
.verdict-strong-hire { background: #EBF5EA; border-left: 3px solid #1A8917; padding: 0.75rem 1rem; border-radius: 0 6px 6px 0; color: #1D1D1F; }
.verdict-hire        { background: #E3F2FD; border-left: 3px solid #1565C0; padding: 0.75rem 1rem; border-radius: 0 6px 6px 0; color: #1D1D1F; }
.verdict-maybe       { background: #FFF3E0; border-left: 3px solid #C47000; padding: 0.75rem 1rem; border-radius: 0 6px 6px 0; color: #1D1D1F; }
.verdict-pass        { background: #FFEBEB; border-left: 3px solid #CC0000; padding: 0.75rem 1rem; border-radius: 0 6px 6px 0; color: #1D1D1F; }

/* Sidebar Nav Item */
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.625rem 0.75rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  color: #6E6E73;
  transition: background 0.12s, color 0.12s;
  margin: 0.125rem 0;
}
.nav-item:hover { background: #EBEBED; color: #1D1D1F; }
.nav-item.active { background: #E8F2FF; color: #0071E3; }

/* Risk Tag */
.risk-tag {
  display: inline-block;
  font-size: 0.75rem;
  padding: 0.25rem 0.625rem;
  border-radius: 4px;
  margin: 0.125rem;
  background: #FFEBEB;
  color: #CC0000;
  font-weight: 500;
}

/* Insight Item */
.insight-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #E8E8ED;
  font-size: 0.875rem;
  color: #6E6E73;
}
.insight-item:last-child { border-bottom: none; }

/* Comparison Column */
.compare-col {
  background: #F5F5F7;
  border-radius: 10px;
  padding: 1.25rem;
  height: 100%;
}
.compare-winner {
  background: #EBF5EA;
  border: 1.5px solid #1A8917;
}

/* Spinner overlay */
.loading-overlay {
  text-align: center;
  padding: 3rem;
  color: #6E6E73;
}
</style>
        """,
        unsafe_allow_html=True,
    )

def page_header(title: str, subtitle: str = "", icon: str = ""):
    """Render a consistent page header."""
    icon_str = f"{icon} " if icon else ""
    st.markdown(
        f"""
<div style="margin-bottom:1.5rem">
  <h1 style="margin:0;font-size:1.75rem;font-weight:700;letter-spacing:-0.025em">{icon_str}{title}</h1>
  {"<p style='margin:0.25rem 0 0;color:#6E6E73;font-size:0.9375rem'>" + subtitle + "</p>" if subtitle else ""}
</div>
""",
        unsafe_allow_html=True,
    )


def section_label(text: str):
    st.markdown(f'<div class="section-header">{text}</div>', unsafe_allow_html=True)


def card_open(extra_class: str = ""):
    st.markdown(f'<div class="aptiva-card {extra_class}">', unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)
