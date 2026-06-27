"""
APTIVA AI — Lucide-style SVG Icon Library
=========================================
All icons are 16×16, stroke-based, stroke-width=2, stroke-linecap/linejoin=round.
Colour is inherited via currentColor — pass a wrapper div with a color to tint.

Usage (inline HTML):
    from ui.icons import icon
    html = f'<span style="color:#1A8917">{icon("check-circle")}</span> Verified'

Usage (inline text label):
    label = f'{icon("briefcase")} {yoe} yrs exp'
"""

_BASE = (
    'xmlns="http://www.w3.org/2000/svg" width="15" height="15" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
    'style="display:inline-block;vertical-align:-2px;flex-shrink:0"'
)

_ICONS: dict[str, str] = {
    # Navigation
    "trophy":        f'<svg {_BASE}><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/></svg>',
    "brain":         f'<svg {_BASE}><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-1.04-4.79A2.5 2.5 0 0 1 6 12V7.5a.5.5 0 0 1 .5-.5 2.5 2.5 0 0 1 2.5-2.5z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 1.04-4.79A2.5 2.5 0 0 0 18 12V7.5a.5.5 0 0 0-.5-.5 2.5 2.5 0 0 0-2.5-2.5z"/></svg>',
    "user":          f'<svg {_BASE}><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "bar-chart":     f'<svg {_BASE}><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "shield-check":  f'<svg {_BASE}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>',
    "git-compare":   f'<svg {_BASE}><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M11 18H8a2 2 0 0 1-2-2V9"/></svg>',
    "activity":      f'<svg {_BASE}><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',

    # Status / Actions
    "check":         f'<svg {_BASE}><polyline points="20 6 9 17 4 12"/></svg>',
    "check-circle":  f'<svg {_BASE}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
    "x":             f'<svg {_BASE}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "x-circle":      f'<svg {_BASE}><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    "alert-triangle":f'<svg {_BASE}><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "info":          f'<svg {_BASE}><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "star":          f'<svg {_BASE}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "zap":           f'<svg {_BASE}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "target":        f'<svg {_BASE}><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "badge-check":   f'<svg {_BASE}><path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76z"/><path d="m9 12 2 2 4-4"/></svg>',
    "loader":        f'<svg {_BASE}><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>',

    # Candidate details
    "briefcase":     f'<svg {_BASE}><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "graduation-cap":f'<svg {_BASE}><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>',
    "code":          f'<svg {_BASE}><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>',
    "folder":        f'<svg {_BASE}><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    "history":       f'<svg {_BASE}><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l4 2"/></svg>',
    "map-pin":       f'<svg {_BASE}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
    "calendar":      f'<svg {_BASE}><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "building":      f'<svg {_BASE}><rect x="4" y="2" width="16" height="20" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M8 10h.01M16 10h.01M8 14h.01M16 14h.01"/></svg>',
    "factory":       f'<svg {_BASE}><path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M17 18h1"/><path d="M12 18h1"/><path d="M7 18h1"/></svg>',

    # UI Actions
    "download":      f'<svg {_BASE}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "upload":        f'<svg {_BASE}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "search":        f'<svg {_BASE}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "filter":        f'<svg {_BASE}><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
    "arrow-right":   f'<svg {_BASE}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    "clock":         f'<svg {_BASE}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "minus":         f'<svg {_BASE}><line x1="5" y1="12" x2="19" y2="12"/></svg>',
}


def icon(name: str, size: int = 15, color: str = "currentColor", extra_style: str = "") -> str:
    """Return the SVG string for a named icon.

    Args:
        name: Icon name (see _ICONS dict).
        size: Width and height in pixels (default 15).
        color: CSS colour string (default 'currentColor').
        extra_style: Additional inline style string.

    Returns:
        SVG HTML string, or empty string if name not found.
    """
    svg = _ICONS.get(name, "")
    if not svg:
        return ""
    # Patch size and color if non-default
    if size != 15 or color != "currentColor":
        svg = svg.replace('width="15"', f'width="{size}"')
        svg = svg.replace('height="15"', f'height="{size}"')
        if color != "currentColor":
            svg = svg.replace('stroke="currentColor"', f'stroke="{color}"')
    if extra_style:
        svg = svg.replace('style="', f'style="{extra_style};')
    return svg


def icon_text(name: str, text: str, color: str = "currentColor", gap: str = "0.4rem", size: int = 15) -> str:
    """Return an HTML span with icon + text, vertically centred."""
    ic = icon(name, size=size, color=color)
    return (
        f'<span style="display:inline-flex;align-items:center;gap:{gap}">'
        f'{ic}<span>{text}</span></span>'
    )
