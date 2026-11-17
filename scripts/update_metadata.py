#!/usr/bin/env python3
"""
Update metadata: README stats, badges, digest.
"""

import json
import re
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
PAPERS_JSON = DATA_DIR / "papers.json"
REPOS_JSON = DATA_DIR / "repos.json"
README_PATH = BASE_DIR / "README.md"
DIGEST_PATH = BASE_DIR / "docs" / "digest.md"


def load_json(path):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def update_readme_stats(papers_db, repos_db):
    """Update the stats in README.md."""
    if not README_PATH.exists():
        print("[WARN] README.md not found")
        return

    papers = papers_db.get("papers", [])
    repos = repos_db.get("repos", [])

    total_papers = len(papers)
    total_repos = len(repos)

    # Count recent papers (last 7 days)
    cutoff = datetime.now()
    recent_papers = 0
    for p in papers:
        if "published_date" in p:
            try:
                pdate = datetime.strptime(p["published_date"], "%Y-%m-%d")
                if (cutoff - pdate).days <= 7:
                    recent_papers += 1
            except:
                pass

    total_stars = sum(r.get("stars", 0) for r in repos)

    # Update README
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Update stats block
    stats_pattern = r"<!-- stats:start -->(.*?)<!-- stats:end -->"
    stats_match = re.search(stats_pattern, content, re.DOTALL)

    if stats_match:
        new_stats = f"""<!-- stats:start -->
- **收录论文**: {total_papers} 篇
- **近 7 天新论文**: {recent_papers} 篇
- **跟踪仓库**: {total_repos} 个
- **累计 star**: {total_stars}
<!-- stats:end -->"""
        content = re.sub(stats_pattern, new_stats, content, flags=re.DOTALL)

        # Update last update date
        today = datetime.now().strftime("%Y-%m-%d")
        content = re.sub(
            r"> 最后自动更新：\d{4}-\d{2}-\d{2}",
            f"> 最后自动更新：{today}",
            content,
        )

        # Update papers badge
        content = re.sub(
            r"![papers]\(.*?\)",
            f"![papers](https://img.shields.io/badge/papers-{total_papers}-green)",
            content,
        )

        with open(README_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Updated README stats: {total_papers} papers, {total_repos} repos, {total_stars} stars")


def generate_digest(papers_db, repos_db):
    """Generate weekly digest."""
    papers = papers_db.get("papers", [])
    cutoff = datetime.now()

    # Group by category
    by_category = {}
    for p in papers:
        cat = p.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(p)

    # Filter recent papers (last 7 days)
    recent_papers = []
    for p in papers:
        if "published_date" in p:
            try:
                pdate = datetime.strptime(p["published_date"], "%Y-%m-%d")
                if (cutoff - pdate).days <= 7:
                    recent_papers.append(p)
            except:
                pass

    recent_papers.sort(key=lambda x: x.get("published_date", ""), reverse=True)

    # Generate digest content
    digest = f"""# 📬 Video Anomaly Detection Weekly Digest

> 自动生成 · {datetime.now().strftime("%Y-%m-%d")}

## 本周新增 ({len(recent_papers)} 篇)

"""

    for p in recent_papers:
        title = p.get("title", "Untitled")
        arxiv_id = p.get("arxiv_id", "N/A")
        date = p.get("published_date", "N/A")
        cat = p.get("category", "unknown")
        url = p.get("url", f"https://arxiv.org/abs/{arxiv_id}")

        digest += f"### [{title}]({url})\n"
        digest += f"- **日期**: {date}\n"
        digest += f"- **arXiv**: [{arxiv_id}]({url})\n"
        digest += f"- **赛道**: {cat}\n"
        if "summary" in p:
            digest += f"- **摘要**: {p['summary'][:200]}...\n"
        digest += "\n"

    if not recent_papers:
        digest += "_本周无新增论文。_\n"

    # Append to existing digest or create new
    if DIGEST_PATH.exists():
        with open(DIGEST_PATH, "r", encoding="utf-8") as f:
            existing = f.read()
        # Remove old digest section
        digest_pattern = r"# 📬 Video Anomaly Detection Weekly Digest.*"
        existing = re.sub(digest_pattern, "", existing, flags=re.DOTALL)
        digest = digest.lstrip("\n") + "\n" + existing
    else:
        digest = f"# 📬 Video Anomaly Detection Weekly Digest\n\n" + digest

    with open(DIGEST_PATH, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"[OK] Updated digest with {len(recent_papers)} new papers")


def main():
    print("Loading data...")
    papers_db = load_json(PAPERS_JSON)
    repos_db = load_json(REPOS_JSON)

    print("Updating README stats...")
    update_readme_stats(papers_db, repos_db)

    print("Generating weekly digest...")
    generate_digest(papers_db, repos_db)

    print("[Done]")


if __name__ == "__main__":
    main()
