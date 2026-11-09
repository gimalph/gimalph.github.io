import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validate_data import validate


ROOT = Path(__file__).resolve().parents[1]


class ValidateDataTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for directory in ("data", "i18n", "schemas"):
            shutil.copytree(ROOT / directory, self.root / directory)
        self.publications_path = self.root / "data/publications.yml"
        self.publications = yaml.safe_load(self.publications_path.read_text(encoding="utf-8"))
        self.paper = self.publications["conference"][0]

    def save_publications(self):
        self.publications_path.write_text(
            yaml.safe_dump(self.publications, allow_unicode=True), encoding="utf-8",
        )

    def assert_publication_error(self, *details):
        self.save_publications()
        errors, _ = validate(self.root)
        expected = ("publications.yml", self.paper["id"], *details)
        self.assertTrue(any(all(detail in error for detail in expected) for error in errors), errors)

    def test_existing_records_with_optional_dates_omitted(self):
        self.paper.pop("accepted_on", None)
        self.paper.pop("online_on", None)
        self.save_publications()
        errors, _ = validate(self.root)
        self.assertEqual(errors, [])

    def test_empty_funding_data(self):
        (self.root / "data/funding.yml").write_text("", encoding="utf-8")
        errors, _ = validate(self.root)
        self.assertEqual(errors, [])

    def test_valid_dates_and_one_way_relationship(self):
        self.paper["accepted_on"] = "2026-06-15"
        self.paper["online_on"] = "2026-08-12"
        self.paper["doi"] = "https://doi.org/10.0000/example"
        self.paper["related_publication_ids"] = [self.publications["journal"][0]["id"]]
        self.save_publications()
        errors, _ = validate(self.root)
        self.assertEqual(errors, [])

    def test_duplicate_id_across_categories(self):
        self.publications["journal"][0]["id"] = self.paper["id"]
        self.assert_publication_error()

    def test_unusual_bibliographic_link_is_a_warning(self):
        self.paper["arxiv"] = "https://doi.org/／ES10.u48550/arXiv.2312.08639"
        self.save_publications()
        errors, warnings = validate(self.root)
        self.assertEqual(errors, [])
        self.assertTrue(any(self.paper["id"] in warning and "arxiv" in warning.lower() for warning in warnings), warnings)

    def test_missing_related_publication(self):
        self.paper["related_publication_ids"] = ["missing-test-publication"]
        self.assert_publication_error("missing-test-publication")

    def test_self_reference(self):
        self.paper["related_publication_ids"] = [self.paper["id"]]
        self.assert_publication_error("related_publication_ids")

    def test_repeated_related_id(self):
        related = self.publications["journal"][0]["id"]
        self.paper["related_publication_ids"] = [related, related]
        self.assert_publication_error("related_publication_ids")

    def test_invalid_dates(self):
        for date in ("2026-02-30", "2026-2-3"):
            with self.subTest(date=date):
                self.paper["accepted_on"] = date
                self.assert_publication_error("accepted_on")

    def test_online_date_requires_doi(self):
        self.paper["online_on"] = "2026-06-15"
        self.paper.pop("doi", None)
        self.assert_publication_error("doi")

    def test_missing_event_translation(self):
        self.paper["accepted_on"] = "2026-06-15"
        self.save_publications()
        translations_path = self.root / "i18n/en.yaml"
        translations = yaml.safe_load(translations_path.read_text(encoding="utf-8"))
        del translations["paper_accepted"]
        translations_path.write_text(yaml.safe_dump(translations), encoding="utf-8")
        errors, _ = validate(self.root)
        self.assertTrue(any("en.yaml" in error and "paper_accepted" in error for error in errors), errors)
