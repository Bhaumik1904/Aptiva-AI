"""
APTIVA AI — Plotly Chart Builders
All charts use the Apple-inspired color system. Clean, minimal, professional.
"""

from typing import Dict, List

import plotly.graph_objects as go
import plotly.express as px


# -- Shared Theme --------------------------------------------------------------
COLORS = {
    "accent":   "#0071E3",
    "success":  "#1A8917",
    "warning":  "#C47000",
    "danger":   "#CC0000",
    "surface":  "#F5F5F7",
    "border":   "#D2D2D7",
    "text":     "#1D1D1F",
    "text_2":   "#6E6E73",
}

BASE_LAYOUT = dict(
    font_family="-apple-system, 'SF Pro Display', 'Inter', sans-serif",
    font_color=COLORS["text"],
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=16, r=16, t=40, b=16),
)

SCORE_COLORS = [COLORS["danger"], COLORS["warning"], COLORS["accent"], COLORS["success"]]


def _score_color(score: float) -> str:
    if score >= 0.75:  return COLORS["success"]
    elif score >= 0.55: return COLORS["accent"]
    elif score >= 0.40: return COLORS["warning"]
    return COLORS["danger"]


# -- Hireability Index Gauge ---------------------------------------------------

def hireability_gauge(hi_score: float, candidate_name: str = "") -> go.Figure:
    """Circular gauge for Hireability Index."""
    color = COLORS["success"] if hi_score >= 80 else COLORS["accent"] if hi_score >= 65 else COLORS["warning"] if hi_score >= 50 else COLORS["danger"]
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=hi_score,
        number={"suffix": "/100", "font": {"size": 32, "color": color, "family": "-apple-system"}},
        title={"text": "Hireability Index", "font": {"size": 13, "color": COLORS["text_2"]}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 0, "showticklabels": False},
            "bar": {"color": color, "thickness": 0.75},
            "bgcolor": COLORS["surface"],
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50],  "color": "#FFEBEB"},
                {"range": [50, 65], "color": "#FFF3E0"},
                {"range": [65, 80], "color": "#E8F2FF"},
                {"range": [80, 100],"color": "#EBF5EA"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.85,
                "value": hi_score,
            },
        },
    ))
    fig.update_layout(**BASE_LAYOUT, height=220)
    return fig


# -- Score Breakdown Bar Chart -------------------------------------------------

def score_breakdown_chart(components: Dict) -> go.Figure:
    """Horizontal bar chart for 7-component score breakdown."""
    labels = ["Title Match", "Skill Trust", "Career Substance", "Experience", "Education", "Location", "Engagement"]
    keys   = ["title", "skills", "career", "experience", "education", "location", "engagement"]
    weights = [0.30, 0.25, 0.20, 0.10, 0.05, 0.05, 0.05]

    scores = [components.get(k, 0) * 100 for k in keys]
    bar_colors = [_score_color(components.get(k, 0)) for k in keys]
    contributions = [s * w * 100 for s, w in zip([components.get(k,0) for k in keys], weights)]

    fig = go.Figure(go.Bar(
        x=scores, y=labels,
        orientation="h",
        marker_color=bar_colors,
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        customdata=contributions,
        hovertemplate="<b>%{y}</b><br>Score: %{x:.0f}/100<br>Contribution: %{customdata:.1f}pts<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        height=280,
        title={"text": "Component Scores", "font": {"size": 13, "color": COLORS["text_2"]}},
        xaxis={"range": [0, 115], "showgrid": False, "showline": False, "zeroline": False},
        yaxis={"showgrid": False},
        showlegend=False,
    )
    return fig


# -- Behavioral Signals Radar --------------------------------------------------

def behavioral_radar(signals: Dict) -> go.Figure:
    """Radar chart for 8 key behavioral signals."""
    from core.behavioral import get_days_inactive

    days_inactive = get_days_inactive(signals)
    recency_score = max(0, min(100, 100 - days_inactive / 3.65))

    categories = [
        "Activity Recency",
        "Response Rate",
        "Profile Completeness",
        "GitHub Activity",
        "Interview Rate",
        "Platform Views",
        "Trust Score",
        "Offer Acceptance",
    ]
    values = [
        recency_score,
        signals.get("recruiter_response_rate", 0) * 100,
        signals.get("profile_completeness_score", 0),
        max(0, signals.get("github_activity_score", 0)),
        signals.get("interview_completion_rate", 0) * 100,
        min(100, signals.get("profile_views_received_30d", 0) * 5),
        min(100, (int(signals.get("verified_email", 0)) + int(signals.get("verified_phone", 0))) * 50),
        signals.get("offer_acceptance_rate", 0) * 100 if signals.get("offer_acceptance_rate", -1) != -1 else 50,
    ]
    values_closed = values + [values[0]]
    cats_closed = categories + [categories[0]]

    fig = go.Figure(go.Scatterpolar(
        r=values_closed,
        theta=cats_closed,
        fill="toself",
        fillcolor=f"rgba(0,113,227,0.12)",
        line={"color": COLORS["accent"], "width": 2},
        hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        height=320,
        polar=dict(
            bgcolor=COLORS["surface"],
            radialaxis={"visible": True, "range": [0, 100], "tickfont": {"size": 10}, "gridcolor": COLORS["border"]},
            angularaxis={"tickfont": {"size": 11}, "gridcolor": COLORS["border"]},
        ),
        title={"text": "Behavioral Signals", "font": {"size": 13, "color": COLORS["text_2"]}},
    )
    return fig


# -- Skill Match Chart ---------------------------------------------------------

def skill_match_chart(skill_gap: Dict) -> go.Figure:
    """Donut chart showing skill match percentage."""
    present = len(skill_gap.get("present_core_skills", []))
    missing = len(skill_gap.get("missing_core_skills", []))
    bonus   = len(skill_gap.get("bonus_skills_matched", []))

    labels = ["Core Skills Present", "Core Skills Missing", "Bonus Skills"]
    values = [present, missing, bonus]
    colors = [COLORS["success"], COLORS["danger"], "#7B3FE4"]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.6,
        marker={"colors": colors, "line": {"color": "#FFFFFF", "width": 2}},
        hovertemplate="%{label}: %{value}<extra></extra>",
        textinfo="none",
    ))
    fig.add_annotation(
        text=f"{skill_gap.get('core_match_pct', 0):.0f}%",
        x=0.5, y=0.5,
        font={"size": 24, "color": COLORS["text"], "family": "-apple-system"},
        showarrow=False,
    )
    fig.update_layout(
        **BASE_LAYOUT,
        height=260,
        title={"text": "Skill Coverage", "font": {"size": 13, "color": COLORS["text_2"]}},
        showlegend=True,
        legend={"font": {"size": 11}},
    )
    return fig


# -- Experience Distribution ---------------------------------------------------

def experience_distribution(candidates: List[Dict]) -> go.Figure:
    """Histogram of years_of_experience."""
    yoe_values = [c["profile"].get("years_of_experience", 0) for c in candidates]
    fig = go.Figure(go.Histogram(
        x=yoe_values,
        nbinsx=20,
        marker={"color": COLORS["accent"], "line": {"color": "#FFFFFF", "width": 1}},
        hovertemplate="YOE: %{x}<br>Count: %{y}<extra></extra>",
    ))
    # Add shaded JD target range
    fig.add_vrect(x0=5, x1=9, fillcolor=COLORS["success"], opacity=0.08, layer="below", line_width=0)
    fig.add_vline(x=6, line_dash="dash", line_color=COLORS["success"], line_width=1.5)
    fig.add_vline(x=8, line_dash="dash", line_color=COLORS["success"], line_width=1.5)
    fig.update_layout(
        **BASE_LAYOUT,
        height=280,
        title={"text": "Experience Distribution (green = JD target range)", "font": {"size": 13, "color": COLORS["text_2"]}},
        xaxis={"title": "Years of Experience", "showgrid": False},
        yaxis={"title": "Candidates", "showgrid": True, "gridcolor": "#F0F0F0"},
    )
    return fig


# -- Top Skills Distribution ---------------------------------------------------

def top_skills_chart(candidates: List[Dict], top_n: int = 15) -> go.Figure:
    """Bar chart of most common skills across all candidates."""
    from collections import Counter
    skill_counts: Counter = Counter()
    for c in candidates:
        for s in c.get("skills", []):
            name = s.get("name", "").strip()
            if name:
                skill_counts[name] += 1

    top = skill_counts.most_common(top_n)
    if not top:
        return go.Figure()

    labels = [t[0] for t in top]
    values = [t[1] for t in top]

    fig = go.Figure(go.Bar(
        x=values[::-1], y=labels[::-1],
        orientation="h",
        marker={"color": COLORS["accent"], "opacity": 0.85},
        hovertemplate="%{y}: %{x} candidates<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        height=max(280, top_n * 22),
        title={"text": f"Top {top_n} Skills Across Dataset", "font": {"size": 13, "color": COLORS["text_2"]}},
        xaxis={"showgrid": False},
        yaxis={"showgrid": False},
    )
    return fig


# -- Location Distribution -----------------------------------------------------

def location_distribution(candidates: List[Dict]) -> go.Figure:
    """Bar chart of candidate locations."""
    from collections import Counter
    loc_counts: Counter = Counter()
    for c in candidates:
        loc = c["profile"].get("location", "Unknown").split(",")[0].strip()
        if loc:
            loc_counts[loc] += 1

    top = loc_counts.most_common(12)
    labels = [t[0] for t in top]
    values = [t[1] for t in top]

    colors_list = [
        COLORS["accent"] if any(p in l.lower() for p in ["pune","noida","delhi","bangalore","bengaluru","hyderabad","mumbai","gurugram"])
        else COLORS["text_2"]
        for l in labels
    ]

    fig = go.Figure(go.Bar(
        x=labels, y=values,
        marker={"color": colors_list},
        hovertemplate="%{x}: %{y} candidates<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        height=280,
        title={"text": "Top Candidate Locations (blue = JD preferred)", "font": {"size": 13, "color": COLORS["text_2"]}},
        xaxis={"showgrid": False},
        yaxis={"showgrid": True, "gridcolor": "#F0F0F0"},
    )
    return fig


# -- Hireability Distribution --------------------------------------------------

def hireability_distribution(scored_candidates: List[Dict]) -> go.Figure:
    """Distribution of Hireability Index scores."""
    hi_scores = []
    for entry in scored_candidates:
        comp = entry.get("components", {})
        hi = comp.get("hireability_index", {})
        if hi:
            hi_scores.append(hi.get("overall", 0))

    if not hi_scores:
        return go.Figure()

    fig = go.Figure(go.Histogram(
        x=hi_scores,
        nbinsx=20,
        marker={"color": COLORS["accent"], "line": {"color": "#FFFFFF", "width": 1}},
        hovertemplate="HI: %{x:.0f}<br>Count: %{y}<extra></extra>",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        height=260,
        title={"text": "Hireability Index Distribution", "font": {"size": 13, "color": COLORS["text_2"]}},
        xaxis={"title": "Hireability Index Score", "showgrid": False},
        yaxis={"title": "Candidates", "showgrid": True, "gridcolor": "#F0F0F0"},
    )
    return fig


# -- Final Score Distribution --------------------------------------------------

def final_score_distribution(scored_candidates: list) -> go.Figure:
    """Distribution of Final Scores — the primary ranking metric."""
    fs_scores = [entry.get("score", 0) for entry in scored_candidates if "score" in entry]
    if not fs_scores:
        return go.Figure()
    top_score = max(fs_scores)
    fig = go.Figure(go.Histogram(
        x=fs_scores, nbinsx=20,
        marker={"color": COLORS["success"], "line": {"color": "#FFFFFF", "width": 1}},
        hovertemplate="Final Score: %{x:.4f}<br>Count: %{y}<extra></extra>",
    ))
    fig.add_vline(x=top_score, line_dash="dash", line_color=COLORS["accent"], line_width=1.5,
                  annotation_text=f"Top: {top_score:.4f}", annotation_position="top right",
                  annotation_font={"size": 11, "color": COLORS["accent"]})
    fig.update_layout(**BASE_LAYOUT, height=260,
        title={"text": "Final Score Distribution (Ranking Metric)", "font": {"size": 13, "color": COLORS["text_2"]}},
        xaxis={"title": "Final Score", "showgrid": False},
        yaxis={"title": "Candidates", "showgrid": True, "gridcolor": "#F0F0F0"})
    return fig


# -- Comparison Spider Chart ---------------------------------------------------

def comparison_radar(comp_a: Dict, comp_b: Dict, label_a: str = "Candidate A", label_b: str = "Candidate B") -> go.Figure:
    """Radar chart comparing two candidates across key dimensions."""
    categories = ["Title", "Skills", "Career", "Experience", "Education", "Location"]
    keys = ["title", "skills", "career", "experience", "education", "location"]

    vals_a = [comp_a.get(k, 0) * 100 for k in keys]
    vals_b = [comp_b.get(k, 0) * 100 for k in keys]

    vals_a_c = vals_a + [vals_a[0]]
    vals_b_c = vals_b + [vals_b[0]]
    cats_c = categories + [categories[0]]

    fig = go.Figure([
        go.Scatterpolar(
            r=vals_a_c, theta=cats_c, fill="toself",
            fillcolor="rgba(0,113,227,0.12)",
            line={"color": COLORS["accent"], "width": 2},
            name=label_a,
        ),
        go.Scatterpolar(
            r=vals_b_c, theta=cats_c, fill="toself",
            fillcolor="rgba(26,137,23,0.10)",
            line={"color": COLORS["success"], "width": 2},
            name=label_b,
        ),
    ])
    fig.update_layout(
        **BASE_LAYOUT,
        height=340,
        polar=dict(
            bgcolor=COLORS["surface"],
            radialaxis={"range": [0, 100], "gridcolor": COLORS["border"], "tickfont": {"size": 10}},
            angularaxis={"gridcolor": COLORS["border"], "tickfont": {"size": 11}},
        ),
        showlegend=True,
        legend={"font": {"size": 11}},
    )
    return fig
