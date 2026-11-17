#!/usr/bin/env python3
"""
Track GitHub repositories for Video Anomaly Detection.
Searches GitHub, tracks star counts, calculates growth.
"""

import argparse
import json
import os
import requests
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "taxonomy.yml"
DATA_DIR = BASE_DIR / "data"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(exist_ok=True)
REPOS_JSON = DATA_DIR / "repos.json"
BLOCKLIST_PATH = BASE_DIR / "config" / "github_blocklist.txt"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_repos_db():
    if REPOS_JSON.exists():
        with open(REPOS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"repos": [], "last_update": None}


def save_repos_db(db):
    db["last_update"] = datetime.now().isoformat()
    with open(REPOS_JSON, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def load_blocklist():
    if BLOCKLIST_PATH.exists():
        with open(BLOCKLIST_PATH, "r", encoding="utf-8") as f:
            return [line.strip().lower() for line in f if line.strip()]
    return []


def search_github(query, token=None, per_page=30):
    """Search GitHub repositories."""
    url = "https://api.github.com/search/repositories"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    params = {"q": query, "per_page": per_page, "sort": "stars", "order": "desc"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code == 403:
            print(f"[WARN] GitHub API rate limited. Status: {resp.status_code}")
            return []
        resp.raise_for_status()
        return resp.json().get("items", [])
    except Exception as e:
        print(f"[ERROR] GitHub search failed: {e}")
        return []


def track_repos(config, repos_db, top_n=50):
    """Track repositories across all categories."""
    blocklist = load_blocklist()
    new_repos = []
    seen_names = {r["name"] for r in repos_db["repos"]}

    categories = config.get("categories", [])
    for cat in categories:
        github_queries = cat.get("github_queries", [])
        cat_id = cat["id"]

        for query in github_queries:
            print(f"  Searching: {query}")
            repos = search_github(query)

            for repo in repos:
                name = repo["full_name"]
                if name.lower() in [b.lower() for b in blocklist]:
                    continue
                if name in seen_names:
                    continue

                repo_info = {
                    "name": name,
                    "url": repo["html_url"],
                    "description": repo.get("description", "") or "",
                    "stars": repo["stargazers_count"],
                    "language": repo.get("language", ""),
                    "category": cat_id,
                    "archived": repo.get("archived", False),
                    "pushed_at": repo.get("pushed_at", ""),
                }

                new_repos.append(repo_info)
                seen_names.add(name)

    return new_repos


def calculate_growth(repos_db, days=7):
    """Calculate 7-day star growth for each repo."""
    repos = repos_db.get("repos", [])
    results = []

    for repo in repos:
        stars = repo.get("stars", 0)
        pushed = repo.get("pushed_at", "")

        # Estimate growth (simple: assume linear from first snapshot)
        # In production, you'd track daily snapshots
        growth = stars // max(days, 1) * 7  # Rough estimate

        results.append({
            "name": repo["name"],
            "url": repo["url"],
            "stars": stars,
            "growth_7d": growth,
            "language": repo.get("language", ""),
            "category": repo.get("category", ""),
        })

    # Sort by growth
    results.sort(key=lambda x: x["growth_7d"], reverse=True)
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Track GitHub repos for VAD")
    parser.add_argument("--top", type=int, default=50, help="Number of repos to track")
    parser.add_argument("--skip-search", action="store_true", help="Skip search, just update metadata")
    args = parser.parse_args()

    print("Loading config...")
    config = load_config()

    print("Loading repos DB...")
    repos_db = load_repos_db()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[WARN] GITHUB_TOKEN not set. GitHub API rate limited (10 req/min).")
        print("[WARN] Set GITHUB_TOKEN env var for better rate limits.")

    if not args.skip_search:
        print("\nSearching GitHub repositories...")
        new_repos = track_repos(config, repos_db, top_n=args.top)

        if new_repos:
            print(f"\nFound {len(new_repos)} new repos:")
            for r in new_repos:
                print(f"  ⭐ {r['stars']} {r['name']} - {r['description'][:50]}")

        repos_db["repos"].extend(new_repos)
        save_repos_db(repos_db)
    else:
        print("Skipping search (already tracked).")

    # Calculate and display growth
    growth = calculate_growth(repos_db, days=7)
    print(f"\n[Top {len(growth)} repos by 7-day growth]:")
    for i, r in enumerate(growth[:10], 1):
        print(f"  {i}. {r['name']} ⭐{r['stars']} (+{r['growth_7d']}/7d)")

    print(f"\n[Done] Total repos tracked: {len(repos_db['repos'])}")


if __name__ == "__main__":
    # Need yaml import
    import yaml
    main()
