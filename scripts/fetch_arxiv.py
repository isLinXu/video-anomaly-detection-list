#!/usr/bin/env python3
"""
Fetch papers from arXiv for Video Anomaly Detection.
Reads config/taxonomy.yml and updates docs/*.md with new papers.
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
import yaml

# Paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "taxonomy.yml"
DATA_DIR = BASE_DIR / "data"
if not DATA_DIR.exists():
    DATA_DIR.mkdir(exist_ok=True)
PAPERS_JSON = DATA_DIR / "papers.json"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_papers_db():
    """Load existing papers database for dedup."""
    if PAPERS_JSON.exists():
        with open(PAPERS_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"papers": [], "last_update": None}


def save_papers_db(db):
    db["last_update"] = datetime.now().isoformat()
    with open(PAPERS_JSON, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def fetch_arxiv_papers(query, start=0, max_results=50):
    """Fetch papers from arXiv API."""
    url = "http://export.arxiv.org/api/query"
    params = {
        "query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERROR] arXiv API request failed: {e}")
        return ""


def parse_arxiv_xml(xml_text):
    """Parse arXiv API XML response into list of paper dicts."""
    papers = []
    entries = re.findall(r"<entry>(.*?)</entry>", xml_text, re.DOTALL)
    for entry in entries:
        paper = {}
        # Title
        title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
        if title_m:
            paper["title"] = re.sub(r"\s+", " ", title_m.group(1)).strip()
        # ID (arXiv ID)
        id_m = re.search(r"<id>http://arxiv\.org/abs/(\d{4}\.\d{5})</id>", entry)
        if id_m:
            paper["arxiv_id"] = id_m.group(1)
            paper["url"] = f"https://arxiv.org/abs/{paper['arxiv_id']}"
        # Authors
        authors_m = re.findall(r"<name>(.*?)</name>", entry)
        if authors_m:
            paper["authors"] = ", ".join(authors_m[:5])
            if len(authors_m) > 5:
                paper["authors"] += f" (+{len(authors_m)-5})"
        # Summary
        summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
        if summary_m:
            paper["summary"] = re.sub(r"\s+", " ", summary_m.group(1)).strip()
        # Published date
        date_m = re.search(r"<published>(.*?)</published>", entry)
        if date_m:
            paper["published_date"] = date_m.group(1)
            try:
                paper["date_obj"] = datetime.strptime(date_m.group(1), "%Y-%m-%d")
            except:
                paper["date_obj"] = datetime.now()
        # Categories
        cats_m = re.findall(r"<category term=\"(.*?)\"", entry)
        paper["categories"] = cats_m
        papers.append(paper)
    return papers


def score_paper(paper, keywords):
    """Score a paper based on keyword matching in title and abstract."""
    score = 0
    title_lower = paper.get("title", "").lower()
    abstract_lower = paper.get("summary", "").lower()

    for kw in keywords.get("strong", []):
        if kw.lower() in title_lower:
            score += 6
        elif kw.lower() in abstract_lower:
            score += 3

    for kw in keywords.get("medium", []):
        if kw.lower() in title_lower:
            score += 4
        elif kw.lower() in abstract_lower:
            score += 2

    for kw in keywords.get("weak", []):
        if kw.lower() in title_lower:
            score += 2
        elif kw.lower() in abstract_lower:
            score += 1

    # Blocklist check
    for block_kw in ["medical imaging anomaly", "network anomaly", "intrusion detection",
                     "industrial defect", "manufacturing anomaly"]:
        if block_kw in abstract_lower:
            return 0  # Filter out

    return score


def should_include(paper, min_score=6):
    """Check if paper should be included based on score."""
    return paper.get("_score", 0) >= min_score


def update_markdown_table(doc_path, papers, category_id):
    """Update the markdown table in a doc file."""
    if not Path(doc_path).exists():
        return

    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the table block
    table_start = content.find(f"<!-- table:start {category_id} -->")
    table_end = content.find(f"<!-- table:end -->")

    if table_start == -1 or table_end == -1:
        print(f"[WARN] Table markers not found in {doc_path}")
        return

    # Build new table content
    new_table = "\n"
    for i, paper in enumerate(papers, 1):
        title = paper.get("title", "Untitled")
        arxiv_id = paper.get("arxiv_id", "N/A")
        arxiv_url = paper.get("url", f"https://arxiv.org/abs/{arxiv_id}")
        date = paper.get("published_date", "N/A")
        authors = paper.get("authors", "Unknown")
        summary = paper.get("summary", "")[:200]

        new_table += f"| {i} | [{title}]({arxiv_url}) | {date} | [{arxiv_id}]({arxiv_url}) | {authors[:80]} |\n"
        if summary:
            new_table += f"   |  |  |  |  | {summary} |\n"

    new_content = (
        content[: table_start + len(f"<!-- table:start {category_id} -->")]
        + new_table
        + content[table_end:]
    )

    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[OK] Updated {doc_path} with {len(papers)} papers")


def fetch_papers_for_category(config, category, papers_db, days=7):
    """Fetch papers for a single category."""
    category_id = category["id"]
    arxiv_queries = category.get("arxiv_queries", [])
    keywords = category.get("keywords", {})
    min_score = config.get("global", {}).get("min_score", 6)

    new_papers = []
    seen_ids = {p["arxiv_id"] for p in papers_db["papers"] if "arxiv_id" in p}

    for query in arxiv_queries:
        print(f"  Fetching: {query}")
        xml = fetch_arxiv_papers(query, max_results=50)
        papers = parse_arxiv_xml(xml)

        for paper in papers:
            # Check date filter
            if "date_obj" in paper:
                cutoff = datetime.now() - timedelta(days=days)
                if paper["date_obj"] < cutoff:
                    continue

            # Score the paper
            paper["_score"] = score_paper(paper, keywords)

            # Dedup
            arxiv_id = paper.get("arxiv_id")
            if arxiv_id and arxiv_id in seen_ids:
                continue

            # Check if should include
            if paper["_score"] >= min_score:
                paper["category"] = category_id
                paper["_score"] = paper["_score"]  # Keep score for logging
                new_papers.append(paper)
                if arxiv_id:
                    seen_ids.add(arxiv_id)

    return new_papers


def main():
    parser = argparse.ArgumentParser(description="Fetch VAD papers from arXiv")
    parser.add_argument("--days", type=int, default=7, help="Days to look back (default: 7)")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be fetched")
    parser.add_argument("--category", type=str, help="Only fetch for a specific category")
    args = parser.parse_args()

    print(f"Loading config from {CONFIG_PATH}")
    config = load_config()

    print(f"Loading papers DB from {PAPERS_JSON}")
    papers_db = load_papers_db()

    all_new_papers = []
    categories = config.get("categories", [])

    for cat in categories:
        if args.category and cat["id"] != args.category:
            continue

        cat_name = cat["name"]
        print(f"\n[Category] {cat_name} ({cat['id']})")

        new_papers = fetch_papers_for_category(config, cat, papers_db, days=args.days)

        if new_papers:
            print(f"  Found {len(new_papers)} new papers")
            for p in new_papers:
                print(f"    [{p['_score']}] {p.get('title', 'Untitled')[:60]}")
            all_new_papers.extend(new_papers)
        else:
            print(f"  No new papers")

    if args.dry_run:
        print(f"\n[Dry run] Would add {len(all_new_papers)} papers")
        return

    # Update papers DB
    papers_db["papers"].extend(all_new_papers)
    save_papers_db(papers_db)

    # Update markdown files
    for cat in categories:
        cat_id = cat["id"]
        doc_path = BASE_DIR / cat["doc"]

        # Get papers for this category
        cat_papers = [p for p in all_new_papers if p.get("category") == cat_id]

        # Also include existing papers for this category from DB
        existing_cat_papers = [
            p for p in papers_db["papers"]
            if p.get("category") == cat_id and "arxiv_id" in p
        ]

        if cat_papers or Path(doc_path).exists():
            # Sort by date (newest first)
            all_cat_papers = existing_cat_papers + cat_papers
            all_cat_papers.sort(key=lambda x: x.get("date_obj", datetime.min), reverse=True)
            update_markdown_table(doc_path, all_cat_papers, cat_id)

    print(f"\n[Done] Total new papers: {len(all_new_papers)}")
    print(f"[Done] Total papers in DB: {len(papers_db['papers'])}")


if __name__ == "__main__":
    main()
