import json
import re
import subprocess
import tempfile
import unittest
from html import unescape
from pathlib import Path
from urllib.parse import unquote

import yaml


ROOT = Path(__file__).resolve().parents[1]


class ResearchPagesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        cls.output = Path(temporary.name) / "public"
        subprocess.run(
            [
                "hugo", "--source", str(ROOT), "--destination", str(cls.output),
                "--cacheDir", str(cls.output.parent / "cache"), "--noBuildLock",
            ],
            check=True,
        )

    def page(self, route):
        return (self.output / route / "index.html").read_text(encoding="utf-8")

    def test_legacy_routes_and_matching_language_links(self):
        for route in ("", "about", "news", "research"):
            ja = f"/{route}/" if route else "/"
            en = f"/en{ja}"
            with self.subTest(route=route):
                self.assertIn(f'href="{en}" hreflang="en"', self.page(ja.strip("/")))
                self.assertIn(f'href="{ja}" hreflang="ja"', self.page(en.strip("/")))
        self.assertIn("https://gimalph.github.io/", self.page("ja"))
        self.assertTrue((self.output / "images/isaac2022/isaac2022-1.jpg").is_file())
        for path, research_url in (
            ("index.json", "https://gimalph.github.io/research/"),
            ("en/index.json", "https://gimalph.github.io/en/research/"),
        ):
            entries = json.loads((self.output / path).read_text(encoding="utf-8"))
            self.assertIn(research_url, [entry["permalink"] for entry in entries])
        for route in ("news", "en/news"):
            page = self.page(route)
            for heading in ("archive", "2023", "2024", "2025", "2026"):
                self.assertIn(f'id="{heading}"', page)

    def test_research_routes_keep_categories_and_display_every_record(self):
        data = yaml.safe_load((ROOT / "data/publications.yml").read_text(encoding="utf-8"))
        papers = [paper for records in data.values() for paper in records]
        paper_ids = [paper["id"] for paper in papers]
        expected_links = [
            (unquote(paper[field]), label)
            for paper in papers
            for field, label in (("doi", "DOI"), ("arxiv", "arXiv"))
            if field in paper
        ]
        for route, workshop_id in (
            ("research", "国際ワークショップでの発表"),
            ("en/research", "presentations-on-international-workshops"),
        ):
            with self.subTest(route=route):
                page = self.page(route)
                self.assertIn('id="journal-papers"', page)
                self.assertIn('id="conference-papers"', page)
                self.assertIn(f'id="{workshop_id}"', page)
                self.assertCountEqual(re.findall(r'<li id="publication-([^"]+)"', page), paper_ids)
                self.assertIn("https://dblp.org/pid/281/6848.html", page)
                links = re.findall(r'<a href="([^"]+)">(DOI|arXiv)</a>', page)
                self.assertCountEqual([(unquote(unescape(url)), label) for url, label in links], expected_links)
                for paper in papers:
                    if paper.get("award"):
                        record = re.search(
                            rf'<li id="publication-{re.escape(paper["id"])}">(.*?)</li>',
                            page, re.S,
                        ).group(1)
                        self.assertRegex(
                            record,
                            r'<div class="publication-award">.*?<span class="publication-icon" aria-hidden="true">🎉</span>',
                        )

    def test_math_titles_are_rendered_as_mathml(self):
        for route in ("research", "en/research"):
            with self.subTest(route=route):
                page = self.page(route)
                self.assertIn("<math", page)
                self.assertIn(r">\mathcal H</annotation>", page)
                self.assertIn(r">n \times n</annotation>", page)

    def test_publications_are_grouped_by_year_with_continuous_numbering(self):
        data = yaml.safe_load((ROOT / "data/publications.yml").read_text(encoding="utf-8"))
        categories = ("journal", "conference", "workshop", "arxiv", "domestic")
        category_icons = {"journal": "📕", "conference": "📘", "workshop": "🧑‍🤝‍🧑", "arxiv": "", "domestic": "🗾"}
        category_prefixes = {"journal": "J", "conference": "C", "workshop": "W", "arxiv": "P", "domestic": "D"}
        years = sorted({str(paper["year"]) for records in data.values() for paper in records}, reverse=True)
        for route, suffix in (("research", "年"), ("en/research", "")):
            lang = "ja" if route == "research" else "en"
            translations = yaml.safe_load((ROOT / f"i18n/{lang}.yaml").read_text(encoding="utf-8"))
            anchors = {
                "journal": "journal-papers",
                "conference": "conference-papers",
                "workshop": "国際ワークショップでの発表" if lang == "ja" else "presentations-on-international-workshops",
                "arxiv": "プレプリント" if lang == "ja" else "preprint-papers",
                "domestic": "国内研究会等での発表" if lang == "ja" else "domestic-presentations",
            }
            page = self.page(route)
            index = re.search(r'<nav\b[^>]*class="publication-index"[^>]*>(.*?)</nav>', page, re.S)
            self.assertIsNotNone(index)
            self.assertIn(
                f'aria-label="{"研究業績の掲載年" if lang == "ja" else "Publication years"}"',
                index.group(0),
            )
            self.assertEqual(
                re.findall(r'href="#publications-([0-9]{4})"', index.group(1)), years,
            )
            sections = re.findall(
                r"<h2\b([^>]*)>(.*?)</h2>(.*?)(?=<h2\b|</article>)",
                page, re.S,
            )
            self.assertEqual(
                [re.sub(r"\s+", "", heading) for _, heading, _ in sections],
                [year + suffix for year in years],
            )
            remaining = {category: len(data[category]) for category in categories}
            for year, (year_attributes, _, section) in zip(years, sections):
                with self.subTest(route=route, year=year):
                    self.assertIn(f'id="publications-{year}"', year_attributes)
                    groups = re.findall(
                        r"<h3\b([^>]*)>(.*?)</h3>(.*?)(?=<h3\b|\Z)",
                        section, re.S,
                    )
                    year_categories = [
                        category for category in categories
                        if any(str(paper["year"]) == year for paper in data[category])
                    ]
                    self.assertEqual(
                        [unescape(re.sub(r"<[^>]+>", "", heading)).strip() for _, heading, _ in groups],
                        [translations[f"publication_{category}"]["other"] for category in year_categories],
                    )
                    for category, (attributes, heading, body) in zip(year_categories, groups):
                        self.assertIn(f'id="{anchors[category]}-{year}"', attributes)
                        self.assertNotIn('class="publication-icon"', heading)
                        expected_ids = [
                            paper["id"] for paper in data[category]
                            if str(paper["year"]) == year
                        ]
                        listing = re.search(r"<ol\b([^>]*)>(.*?)</ol>", body, re.S)
                        self.assertIsNotNone(listing)
                        self.assertEqual(
                            re.findall(r'<li id="publication-([^"]+)"', listing.group(2)),
                            expected_ids,
                        )
                        self.assertRegex(listing.group(1), r"\breversed\b")
                        self.assertRegex(listing.group(1), rf'\bstart="{remaining[category]}"')
                        records = re.findall(r'<li id="publication-[^"]+">(.*?)</li>', listing.group(2), re.S)
                        for offset, record in enumerate(records):
                            label = re.search(
                                r'<span class="publication-label">(.*?)</span>\s*<div class="publication-content">',
                                record, re.S,
                            )
                            self.assertIsNotNone(label)
                            icons = re.findall(
                                r'<span class="publication-icon" aria-hidden="true">(.*?)</span>',
                                label.group(1), re.S,
                            )
                            self.assertEqual(icons, [category_icons[category]] if category_icons[category] else [])
                            number = remaining[category] - offset
                            text = re.sub(r'<span class="publication-icon"[^>]*>.*?</span>', "", label.group(1), flags=re.S)
                            self.assertEqual(text.strip(), f"{category_prefixes[category]}{number}.")
                        remaining[category] -= len(expected_ids)
                        if category == "domestic":
                            count = sum(
                                str(paper["year"]) == year and paper.get("presenter") == "儀間 達也"
                                for paper in data[category]
                            )
                            message = f"うち、儀間が発表したもの {count} 件" if lang == "ja" else f"Presentations by Tatsuya Gima: {count}"
                            self.assertIn(message, body)
            for anchor in anchors.values():
                self.assertEqual(page.count(f'id="{anchor}"'), 1)

    def test_cv_routes_render_funding_data_or_empty_state(self):
        data = yaml.safe_load((ROOT / "data/funding.yml").read_text(encoding="utf-8"))
        for route, message in (
            ("about", "掲載している研究費情報はありません。"),
            ("en/about", "No funding records are listed."),
        ):
            with self.subTest(route=route):
                page = self.page(route)
                if data:
                    self.assertIn('class="funding-list"', page)
                else:
                    self.assertIn(message, page)
