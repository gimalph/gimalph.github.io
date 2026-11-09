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
        for route in ("", "about", "news", "research", "funding"):
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

    def test_math_titles_are_rendered_as_mathml(self):
        for route in ("research", "en/research"):
            with self.subTest(route=route):
                page = self.page(route)
                self.assertIn("<math", page)
                self.assertIn(r">\mathcal H</annotation>", page)
                self.assertIn(r">n \times n</annotation>", page)

    def test_funding_routes_render_existing_data_or_empty_state(self):
        data = yaml.safe_load((ROOT / "data/funding.yml").read_text(encoding="utf-8"))
        for route, message in (
            ("funding", "掲載している研究費情報はありません。"),
            ("en/funding", "No funding records are listed."),
        ):
            with self.subTest(route=route):
                page = self.page(route)
                if data:
                    self.assertIn('class="funding-list"', page)
                else:
                    self.assertIn(message, page)
