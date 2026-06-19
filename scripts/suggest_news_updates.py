#!/usr/bin/env python3
"""Suggest news.md entries from changes in data/publications.yml.

The script compares the current publications.yml with the version in git
HEAD, detects added/changed publication records, and prints draft entries for
content/news.md and content/en/news.md. It does not edit files.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit("PyYAML is required: python3 -m pip install PyYAML") from exc


PUBLICATIONS_PATH = "data/publications.yml"
NEWS_PATHS = ("content/news.md", "content/en/news.md")
MY_NAME_EN = "Tatsuya Gima"

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def run_git(args: list[str], cwd: Path, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def repo_root() -> Path:
    output = run_git(["rev-parse", "--show-toplevel"], Path.cwd())
    return Path(output.strip())


def load_yaml_text(text: str, source: str) -> dict[str, Any]:
    try:
        data = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"Failed to parse {source}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"{source} must contain a top-level mapping")
    return data


def read_base_publications(root: Path, base: str) -> dict[str, Any]:
    text = run_git(["show", f"{base}:{PUBLICATIONS_PATH}"], root)
    return load_yaml_text(text, f"{base}:{PUBLICATIONS_PATH}")


def read_current_publications(root: Path, staged: bool) -> dict[str, Any]:
    if staged:
        text = run_git(["show", f":{PUBLICATIONS_PATH}"], root)
        return load_yaml_text(text, f"index:{PUBLICATIONS_PATH}")
    text = (root / PUBLICATIONS_PATH).read_text(encoding="utf-8")
    return load_yaml_text(text, PUBLICATIONS_PATH)


def normalize_title(title: Any) -> str:
    return re.sub(r"\s+", " ", str(title or "").strip()).casefold()


def flatten(data: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    records: dict[tuple[str, str], dict[str, Any]] = {}
    for category, items in data.items():
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            title = normalize_title(item.get("title"))
            if not title:
                continue
            key = (str(category), title)
            item_copy = dict(item)
            item_copy["_category"] = str(category)
            item_copy["_index"] = index
            records[key] = item_copy
    return records


def changed_records(
    old_data: dict[str, Any], new_data: dict[str, Any], include_modified: bool
) -> list[dict[str, Any]]:
    old = flatten(old_data)
    new = flatten(new_data)
    changes: list[dict[str, Any]] = []
    for key, item in new.items():
        old_item = old.get(key)
        if old_item is None:
            item = dict(item)
            item["_change"] = "added"
            changes.append(item)
        elif include_modified and comparable(item) != comparable(old_item):
            item = dict(item)
            item["_change"] = "modified"
            changes.append(item)
    return sorted(changes, key=sort_key)


def comparable(item: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in item.items() if not key.startswith("_")}


def sort_key(item: dict[str, Any]) -> tuple[int, int, str, int]:
    year = int(str(item.get("year") or guess_year(item) or 0))
    month = month_number(item.get("month")) or guess_month(item) or 0
    category_order = {
        "conference": 0,
        "journal": 1,
        "arxiv": 2,
        "workshop": 3,
        "domestic": 4,
    }.get(str(item.get("_category")), 9)
    return (-year, -month, str(item.get("title", "")), category_order)


def month_number(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text.isdigit():
        month = int(text)
        return month if 1 <= month <= 12 else None
    return MONTHS.get(text)


def month_en(number: int | None) -> str:
    if not number:
        return "MONTH"
    return dt.date(2000, number, 1).strftime("%B")


def month_ja(number: int | None) -> str:
    return f"{number}月" if number else "MONTH月"


def guess_arxiv_date(item: dict[str, Any]) -> tuple[int | None, int | None]:
    arxiv = str(item.get("arxiv") or "")
    match = re.search(r"(\d{2})(\d{2})\.\d+", arxiv)
    if not match:
        return None, None
    year = 2000 + int(match.group(1))
    month = int(match.group(2))
    if not 1 <= month <= 12:
        return year, None
    return year, month


def guess_year(item: dict[str, Any]) -> int | None:
    if item.get("year"):
        return int(str(item["year"]))
    year, _month = guess_arxiv_date(item)
    return year


def guess_month(item: dict[str, Any]) -> int | None:
    if item.get("month"):
        return month_number(item["month"])
    _year, month = guess_arxiv_date(item)
    return month


def title(item: dict[str, Any]) -> str:
    return re.sub(r"\s+", " ", str(item.get("title", "")).strip())


def venue(item: dict[str, Any]) -> str:
    return str(item.get("booktitle") or item.get("journal") or "VENUE").strip()


def authors_without_me(item: dict[str, Any]) -> str:
    authors = item.get("author") or []
    if not isinstance(authors, list):
        return "COAUTHORS"
    coauthors = [str(author).strip() for author in authors if str(author).strip() != MY_NAME_EN]
    if not coauthors:
        return ""
    if len(coauthors) == 1:
        return coauthors[0]
    if len(coauthors) == 2:
        return f"{coauthors[0]} and {coauthors[1]}"
    return ", ".join(coauthors[:-1]) + f", and {coauthors[-1]}"


def authors_with_label(item: dict[str, Any]) -> str:
    coauthors = authors_without_me(item)
    return f" with {coauthors}" if coauthors else ""


def venue_link(item: dict[str, Any]) -> str:
    value = venue(item)
    if item.get("doi"):
        return f"_{value}_ ([link]({item['doi']}))"
    return f"_{value}_"


def short_venue_name(item: dict[str, Any]) -> str:
    text = venue(item)
    match = re.search(r"\(([A-Z0-9^ ]+ \d{4})\)", text)
    if match:
        return match.group(1).strip()
    match = re.search(r"\b([A-Z][A-Z0-9^]+)\s*(\d{4})\b", text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return text


def news_lines(item: dict[str, Any], lang: str) -> list[str]:
    category = str(item.get("_category"))
    year = guess_year(item)
    month = guess_month(item)
    paper = title(item)
    with_authors = authors_with_label(item)
    short_venue = short_venue_name(item)
    award = str(item.get("award") or "").strip()
    change = " [modified]" if item.get("_change") == "modified" else ""

    if lang == "ja":
        prefix = f"1. {icon(category, award)}{month_ja(month)}:"
        if category == "conference":
            sentence = f"{prefix} 以下の論文が [_{short_venue}_](TODO) に採択されました"
            if award:
                sentence += f"（{award}）"
            sentence += f".{change}"
        elif category == "journal":
            sentence = f"{prefix} 以下の論文が {venue_link(item)} に採択・出版されました.{change}"
        elif category == "arxiv":
            sentence = f"{prefix} 以下の論文を arXiv に公開しました.{change}"
        elif category == "workshop":
            sentence = f"{prefix} 以下の発表が [_{short_venue}_](TODO) に採択されました.{change}"
        elif category == "domestic":
            sentence = f"{prefix} {venue(item)} にて以下の発表に関わりました.{change}"
        else:
            sentence = f"{prefix} 以下の項目を追加しました.{change}"
        return [f"## {year or 'YEAR'}", sentence, f"\t- ``{paper}''{with_authors}"]

    prefix = f"1. {icon(category, award)}{month_en(month)}:"
    if category == "conference":
        sentence = f"{prefix} The following paper has been accepted to [_{short_venue}_](TODO)"
        if award:
            award_label = award if "award" in award.lower() else f"{award} Award"
            sentence += f" and received the ``{award_label}''"
        sentence += f".{change}"
    elif category == "journal":
        sentence = f"{prefix} The following paper has been accepted/published in {venue_link(item)}.{change}"
    elif category == "arxiv":
        sentence = f"{prefix} The following paper has been posted on arXiv.{change}"
    elif category == "workshop":
        sentence = f"{prefix} The following presentation has been accepted to [_{short_venue}_](TODO).{change}"
    elif category == "domestic":
        sentence = f"{prefix} I was involved in the following presentation at {venue(item)}.{change}"
    else:
        sentence = f"{prefix} The following item has been added.{change}"
    return [f"## {year or 'YEAR'}", sentence, f"\t- ``{paper}''{with_authors}"]


def icon(category: str, award: str = "") -> str:
    icons = {
        "conference": "📘",
        "journal": "📕",
        "arxiv": "",
        "workshop": "🧑‍🤝‍🧑",
        "domestic": "🗾",
    }
    prefix = icons.get(category, "")
    if award:
        prefix = "🎉" + prefix
    return prefix


def existing_news_titles(root: Path) -> set[str]:
    titles: set[str] = set()
    pattern = re.compile(r"[`'\"]{1,2}([^`'\"]+)[`'\"]{1,2}")
    for relpath in NEWS_PATHS:
        path = root / relpath
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            titles.add(normalize_title(match.group(1)))
    return titles


def print_suggestions(items: list[dict[str, Any]], root: Path) -> None:
    existing = existing_news_titles(root)
    if not items:
        print("No added publication records were found.")
        return

    print("# Suggested news entries")
    print()
    print(
        "Note: months are inferred from publications.yml (or the arXiv id). "
        "Replace TODO links and adjust acceptance dates if needed."
    )
    print()
    for item in items:
        already = normalize_title(item.get("title")) in existing
        status = "already appears in news" if already else "not found in news"
        print(f"## {item['_category']}: {title(item)} ({item['_change']}, {status})")
        print()
        print("Japanese:")
        print("```markdown")
        print("\n".join(news_lines(item, "ja")))
        print("```")
        print()
        print("English:")
        print("```markdown")
        print("\n".join(news_lines(item, "en")))
        print("```")
        print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Suggest content/news.md entries from publications.yml changes."
    )
    parser.add_argument(
        "--base",
        default="HEAD",
        help="git revision to compare from (default: HEAD)",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="compare the index version of publications.yml instead of the working tree",
    )
    parser.add_argument(
        "--include-modified",
        action="store_true",
        help="also suggest entries for modified existing publication records",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    old_data = read_base_publications(root, args.base)
    new_data = read_current_publications(root, args.staged)
    items = changed_records(old_data, new_data, args.include_modified)
    print_suggestions(items, root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
