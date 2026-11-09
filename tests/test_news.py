import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOI = "https://doi.org/10.0000/example"


class NewsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temporary.cleanup)
        site = Path(temporary.name)
        (site / "hugo.yaml").write_text(
            """baseURL: https://example.org/
defaultContentLanguage: ja
disableKinds: [home, taxonomy, term]
languages:
  ja:
    contentDir: content/ja
    weight: 1
  en:
    contentDir: content/en
    weight: 2
markup:
  goldmark:
    extensions:
      passthrough:
        enable: true
        delimiters:
          inline: [['$', '$']]
""",
            encoding="utf-8",
        )
        templates = (
            "partials/collect-events.html",
            "shortcodes/recent-news.html",
            "shortcodes/funding.html",
            "_markup/render-passthrough.html",
        )
        for name in templates:
            path = site / "layouts" / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "layouts" / name, path)
        shutil.copytree(ROOT / "i18n", site / "i18n")
        pages = {"all": "", "year": " months=12", "top": " limit=2 months=12"}
        for lang in ("ja", "en"):
            content = site / "content" / lang
            content.mkdir(parents=True)
            for name, options in pages.items():
                (content / f"{name}.md").write_text(
                    f'---\ntitle: "News fixture"\ndraft: true\n---\n\n'
                    f'{{{{< recent-news{options} >}}}}\n',
                    encoding="utf-8",
                )
            (content / "funding.md").write_text(
                '---\ntitle: "Funding fixture"\ndraft: true\n---\n\n{{< funding >}}\n',
                encoding="utf-8",
            )

        data = {
            "publications": {
                "conference": [
                    {
                        "title": "Example Paper",
                        "booktitle": "Example Conference",
                        "accepted_on": "2026-06-15",
                        "online_on": "2026-06-16",
                        "doi": DOI,
                    },
                    {"title": "Same-day paper with $x^2$", "accepted_on": "2026-06-15"},
                    {"title": "Undated Paper", "year": 2026, "month": 6, "doi": DOI},
                ],
            },
            "funding": [
                {
                    "title": "研究課題名",
                    "title_en": "Example Grant",
                    "agency": "助成機関名",
                    "agency_en": "Example Agency",
                    "period": "2026–2028",
                    "number": "GRANT-26",
                    "accepted_on": "2026-06-15",
                },
            ],
            "positions": [
                {"title": "研究員", "title_en": "Research Fellow", "started_on": "2026-01-01"},
            ],
            "awards": [
                {"award": "賞の名前", "award_en": "Example Award", "received_on": "2025-06-15"},
            ],
            "news_extra": [
                {"text_ja": "境界のお知らせ", "text_en": "Cutoff update", "date": "2025-06-16"},
                {"text_ja": "未来のお知らせ", "text_en": "Future update", "date": "2026-06-17"},
            ],
        }
        (site / "data").mkdir()
        for name, value in data.items():
            # JSON syntax is a YAML subset and keeps the fixtures dependency-free.
            (site / "data" / f"{name}.yml").write_text(json.dumps(value), encoding="utf-8")

        # Use the real shortcodes and partials with a minimal fixture page.
        (site / "layouts" / "page.html").write_text("{{ .Content }}", encoding="utf-8")
        cls.output = site / "public"
        subprocess.run(
            [
                "hugo", "--source", str(site), "--cacheDir", str(site / "cache"),
                "--buildDrafts", "--clock", "2026-06-15T15:01:00Z",
            ],
            check=True,
            env={**os.environ, "TZ": "UTC"},
        )

    def page(self, name, lang="en"):
        prefix = self.output / "en" if lang == "en" else self.output
        return (prefix / name / "index.html").read_text(encoding="utf-8")

    def test_separate_events_stable_ties_and_tokyo_date(self):
        html = self.page("all")
        self.assertEqual(
            re.findall(r'datetime="([\d-]+)"', html),
            [
                "2026-06-16", "2026-06-15", "2026-06-15", "2026-06-15",
                "2026-01-01", "2025-06-16", "2025-06-15",
            ],
        )
        ordered_text = [
            "is now available online",
            "was accepted to Example Conference",
            "Same-day paper",
            "Example Grant",
        ]
        positions = [html.index(text) for text in ordered_text]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(html.count(f'href="{DOI}"'), 1)
        self.assertNotIn("Undated Paper", html)
        self.assertNotIn("Future update", html)

    def test_localized_months_and_year_headings(self):
        en, ja = self.page("all"), self.page("all", "ja")
        self.assertIn(">June 2026</time>", en)
        self.assertIn(">2026年6月</time>", ja)
        self.assertIn("研究課題名", ja)
        self.assertIn("Research Fellow", en)
        self.assertIn("Example Award", en)
        self.assertIn("<math ", en)
        self.assertEqual(re.findall(r'class="news-year">(\d+)</h3>', en), ["2026", "2025"])

    def test_period_and_count_limits(self):
        year = self.page("year")
        self.assertIn("Cutoff update", year)
        self.assertNotIn("Example Award", year)
        self.assertEqual(self.page("top").count('class="news-date"'), 2)

    def test_funding_record_is_visible_in_both_languages(self):
        ja, en = self.page("funding", "ja"), self.page("funding")
        self.assertIn("研究課題名", ja)
        self.assertIn("助成機関名", ja)
        self.assertIn("Example Grant", en)
        self.assertIn("Example Agency", en)
        self.assertIn("2026–2028", en)
        self.assertIn("GRANT-26", en)


if __name__ == "__main__":
    unittest.main()
