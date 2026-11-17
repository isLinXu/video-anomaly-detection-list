#!/usr/bin/env python3
"""
Render charts as SVG for README and docs.
"""

import json
import os
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PAPERS_JSON = DATA_DIR / "papers.json"
ASSETS_DIR = BASE_DIR / "assets"
if not ASSETS_DIR.exists():
    ASSETS_DIR.mkdir(exist_ok=True)

# Theme
THEME = os.environ.get("THEME", "dark")
BGC = "#1e1e2e" if THEME == "dark" else "#ffffff"
FG = "#cdd6f4" if THEME == "dark" else "#1e1e2e"
ACCENT = "#a6e0f7" if THEME == "dark" else "#d2040c"


def load_papers_db():
    if PAPERS_JSON.exists():
        with open(PAPERS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"papers": []}


def render_banner(papers_db):
    """Render a banner SVG."""
    total_papers = len(papers_db.get("papers", []))
    width, height = 680, 120

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{BGC}" rx="8"/>
  <text x="40" y="45" fill="{ACCENT}" font-size="28" font-weight="bold">🎬 Video Anomaly Detection</text>
  <text x="40" y="80" fill="{FG}" font-size="16">追踪论文: {total_papers} 篇 · 自动生成</text>
</svg>"""

    path = ASSETS_DIR / "banner.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[OK] Banner -> {path}")


def render_category_chart(papers_db):
    """Render a category distribution chart."""
    papers = papers_db.get("papers", [])
    category_counts = {}
    for p in papers:
        cat = p.get("category", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    if not category_counts:
        return

    width, height = 680, 400
    bar_width = 60
    max_count = max(category_counts.values())
    chart_height = 300

    emoji_map = {
        "weakly-supervised-vad": "👁️",
        "semi-supervised-vad": "🔍",
        "fully-supervised-vad": "📊",
        "open-world-vad": "🌍",
        "video-anomaly-retrieval": "🔎",
        "video-anomaly-understanding": "🧠",
        "skeleton-based-vad": "🦴",
        "prompt-based-vad": "💬",
        "self-supervised-vad": "🔄",
        "vad-surveys": "📚",
        "vad-benchmarks": "🏋",
    }

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{BGC}" rx="8"/>
  <text x="340" y="30" text-anchor="middle" fill="{ACCENT}" font-size="20" font-weight="bold">各赛道论文数量</text>
"""

    sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    for i, (cat, count) in enumerate(sorted_cats):
        bar_height = (count / max_count) * chart_height
        x = 60 + i * 80
        y = height - 60 - bar_height

        emoji = emoji_map.get(cat, "📄")
        label = cat.replace("-", " ").title()

        svg += f"""  <rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" fill="{ACCENT}" rx="4"/>
  <text x="{x + bar_width/2}" y="{y - 10}" text-anchor="middle" fill="{FG}" font-size="14">{count}</text>
  <text x="{x + bar_width/2}" y="{height - 40}" text-anchor="middle" fill="{FG}" font-size="11">{emoji}</text>
  <text x="{x + bar_width/2}" y="{height - 25}" text-anchor="middle" fill="{FG}" font-size="9" transform="rotate(-30 {x + bar_width/2} {height - 25})">{label}</text>
"""

    svg += "</svg>"

    path = ASSETS_DIR / "category_chart.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[OK] Category chart -> {path}")


def render_trend_chart(papers_db):
    """Render a trend chart (if time series data available)."""
    papers = papers_db.get("papers", [])

    if not papers:
        return

    # Group by week
    week_counts = {}
    for p in papers:
        if "published_date" in p:
            try:
                date = datetime.strptime(p["published_date"], "%Y-%m-%d")
                week = date.strftime("%Y-W%W")
                week_counts[week] = week_counts.get(week, 0) + 1
            except:
                pass

    if not week_counts:
        return

    sorted_weeks = sorted(week_counts.keys())
    counts = [week_counts[w] for w in sorted_weeks]

    width, height = 680, 300
    chart_height = 200
    padding = 60

    max_count = max(counts) if counts else 1

    svg = f"""<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="{BGC}" rx="8"/>
  <text x="340" y="30" text-anchor="middle" fill="{ACCENT}" font-size="20" font-weight="bold">论文发表趋势</text>
"""

    # Draw line
    for i in range(len(sorted_weeks)):
        x = padding + (i / max(len(sorted_weeks) - 1, 1)) * (width - 2 * padding)
        y = height - padding - (counts[i] / max_count) * (chart_height)
        if i == 0:
            svg += f'  <path d="M {x} {y}" fill="none" stroke="{ACCENT}" stroke-width="2"/>\n'
        else:
            prev_x = padding + ((i - 1) / max(len(sorted_weeks) - 1, 1)) * (width - 2 * padding)
            prev_y = height - padding - (counts[i - 1] / max_count) * (chart_height)
            svg += f'  <path d="M {prev_x} {prev_y} L {x} {y}" fill="none" stroke="{ACCENT}" stroke-width="2"/>\n'

    # Points
    for i in range(len(sorted_weeks)):
        x = padding + (i / max(len(sorted_weeks) - 1, 1)) * (width - 2 * padding)
        y = height - padding - (counts[i] / max_count) * (chart_height)
        svg += f'  <circle cx="{x}" cy="{y}" r="4" fill="{ACCENT}"/>\n'
        svg += f'  <text x="{x}" y="{y - 10}" text-anchor="middle" fill="{FG}" font-size="10">{counts[i]}</text>\n'

    svg += "</svg>"

    path = ASSETS_DIR / "trend_chart.svg"
    with open(path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"[OK] Trend chart -> {path}")


def main():
    print("Loading papers DB...")
    papers_db = load_papers_db()

    print("Rendering charts...")
    render_banner(papers_db)
    render_category_chart(papers_db)
    render_trend_chart(papers_db)

    print("[Done]")


if __name__ == "__main__":
    main()
