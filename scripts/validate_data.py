#!/usr/bin/env python3
"""Validate the site's YAML and references before building with Hugo."""

import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError


DATASETS = ("publications", "funding", "positions", "awards", "news_extra")
EVENT_KINDS = (
    "paper_accepted",
    "paper_online",
    "fund_awarded",
    "position_started",
    "award_received",
    "news_extra",
)
ARXIV_URL = re.compile(
    r"https?://(?:(?:www\.)?arxiv\.org/(?:abs|pdf)/|(?:dx\.)?doi\.org/10\.48550/arxiv\.)",
    re.IGNORECASE,
)


def schema_error(file, data, error):
    path = list(error.absolute_path)
    record_path_length = 2 if file == "data/publications.yml" else 1
    record = data
    record_path = path[:record_path_length]
    for key in record_path:
        record = record[key]
    if len(record_path) == record_path_length and isinstance(record, dict):
        record_id = record.get("id")
    else:
        record_id = None
    location = ".".join(map(str, path)) or "root"
    label = f"{file} [{record_id}] {location}" if record_id else f"{file} {location}"
    if error.validator == "format" and error.validator_value == "date":
        return f"{label}: {error.instance!r} is not a real calendar date"
    if error.validator == "type" and path and str(path[-1]).endswith(("_on", "date")):
        return f'{label}: use a quoted date string in "YYYY-MM-DD" format'
    return f"{label}: {error.message}"


def check_publications(data, errors, warnings):
    papers = {}
    for category, records in data.items():
        for record in records:
            paper_id = record["id"]
            label = f"data/publications.yml [{paper_id}]"
            if paper_id in papers:
                previous = papers[paper_id][0]
                errors.append(f"{label}: duplicate publication ID in {previous} and {category}")
            papers[paper_id] = (category, record)
            if record.get("online_on") and not record.get("doi"):
                errors.append(f"{label}: online_on requires doi")
            if record.get("arxiv") and not ARXIV_URL.match(record["arxiv"]):
                warnings.append(f"{label} arxiv: unusual arXiv URL {record['arxiv']!r}")

    for paper_id, (_, record) in papers.items():
        label = f"data/publications.yml [{paper_id}] related_publication_ids"
        seen = set()
        for related_id in record.get("related_publication_ids", []):
            if related_id in seen:
                errors.append(f"{label}: duplicate related ID {related_id!r}")
            if related_id == paper_id:
                errors.append(f"{label}: cannot reference itself")
            elif related_id not in papers:
                errors.append(f"{label}: unknown publication ID {related_id!r}")
            seen.add(related_id)


def validate(root: Path) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for name in DATASETS:
        file = f"data/{name}.yml"
        schema_file = f"schemas/{name}.schema.json"
        try:
            data = yaml.safe_load((root / file).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"{file}: {exc}")
            continue
        try:
            schema = json.loads((root / schema_file).read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except (OSError, ValueError, SchemaError) as exc:
            errors.append(f"{schema_file}: {exc}")
            continue
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        issues = list(validator.iter_errors(data))
        errors.extend(schema_error(file, data, issue) for issue in issues)
        if name == "publications" and not issues:
            check_publications(data, errors, warnings)

    for lang in ("ja", "en"):
        file = f"i18n/{lang}.yaml"
        try:
            translations = yaml.safe_load((root / file).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            errors.append(f"{file}: {exc}")
            continue
        if not isinstance(translations, dict):
            errors.append(f"{file}: expected a translation mapping")
            continue
        for kind in EVENT_KINDS:
            text = translations.get(kind)
            if isinstance(text, dict):
                text = text.get("other")
            if not isinstance(text, str) or not text.strip():
                errors.append(f"{file}: missing translation for {kind}")
    return errors, warnings


def main() -> int:
    errors, warnings = validate(Path(__file__).resolve().parents[1])
    for label, messages in (("warning", warnings), ("error", errors)):
        for message in messages:
            print(f"{label}: {message}", file=sys.stderr)
    if errors:
        return 1
    print("Site data is valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
