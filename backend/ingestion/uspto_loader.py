import json
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from database import (
    create_inventor,
    create_patent,
    create_patent_inventor_link,
    get_inventor_by_name,
    get_patent_by_publication_number,
    get_patent_inventor_link,
    search_patents_by_keyword,
)

PATENTSVIEW_API_URL = os.getenv(
    "PATENTSVIEW_API_URL",
    "https://search.patentsview.org/api/v1/patent/",
)
PATENTSVIEW_API_KEY = os.getenv("PATENTSVIEW_API_KEY", "").strip()
DEFAULT_SYNC_LIMIT = int(os.getenv("PATENT_SYNC_LIMIT", "10"))


def _has_real_patentsview_key() -> bool:
    if not PATENTSVIEW_API_KEY:
        return False

    placeholder_markers = ("your-patentsview-key", "replace-me", "example")
    lowered_key = PATENTSVIEW_API_KEY.lower()
    return not any(marker in lowered_key for marker in placeholder_markers)


def split_name(full_name: str) -> Tuple[str, str]:
    cleaned_name = " ".join((full_name or "").strip().split())

    if not cleaned_name:
        return "", ""

    name_parts = cleaned_name.split(" ")

    if len(name_parts) == 1:
        return name_parts[0], ""

    return name_parts[0], " ".join(name_parts[1:])


def infer_technology_domain(*values: str) -> str:
    combined = " ".join(value for value in values if value).lower()

    domain_keywords = {
        "AI/ML": ["ai", "artificial intelligence", "machine learning", "neural", "llm", "computer vision"],
        "Health": ["health", "medical", "therapy", "drug", "clinical", "diagnostic", "biomedical"],
        "Manufacturing": ["manufacturing", "robot", "industrial", "factory", "assembly", "machining"],
    }

    for domain, keywords in domain_keywords.items():
        if any(keyword in combined for keyword in keywords):
            return domain

    return "General"


def get_or_create_inventor(full_name: str, affiliation: str = "Imported from Internet") -> Optional[int]:
    first_name, last_name = split_name(full_name)

    if not first_name and not last_name:
        return None

    existing = get_inventor_by_name(first_name, last_name)

    if existing:
        return existing["inventor_id"]

    created = create_inventor(first_name, last_name, affiliation, "")
    return created["inventor_id"]


def link_patent_to_inventor(patent_id: int, inventor_id: int) -> bool:
    existing = get_patent_inventor_link(patent_id, inventor_id)

    if existing:
        return False

    create_patent_inventor_link(patent_id, inventor_id)
    return True


def save_patent(
    title: str,
    publication_number: str,
    technology_domain: str,
    abstract: str = "",
    source: str = "Internet",
    assignee: str = "",
    inventor_names: str = "",
) -> Tuple[int, bool]:
    existing_patent = get_patent_by_publication_number(publication_number)

    if existing_patent:
        return existing_patent["patent_id"], False

    created_patent = create_patent(
        title=title,
        publication_number=publication_number,
        technology_domain=technology_domain,
        abstract=abstract,
        source=source,
        assignee=assignee,
        inventor_names=inventor_names,
    )
    return created_patent["patent_id"], True


def search_local_patents(keyword: str) -> List[Dict[str, Any]]:
    return search_patents_by_keyword(keyword)


def _extract_api_records(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("patents", "data", "results", "items"):
        records = payload.get(key)
        if isinstance(records, list):
            return records

    return []


def _build_inventor_names(record: Dict[str, Any]) -> str:
    inventors = record.get("inventors", []) or []
    names: List[str] = []

    for inventor in inventors:
        first_name = (inventor.get("inventor_name_first") or "").strip()
        last_name = (inventor.get("inventor_name_last") or "").strip()
        full_name = " ".join(part for part in (first_name, last_name) if part)

        if full_name:
            names.append(full_name)

    return ", ".join(names)


def _build_assignee_name(record: Dict[str, Any]) -> str:
    assignees = record.get("assignees", []) or []

    for assignee in assignees:
        organization = (assignee.get("assignee_organization") or "").strip()
        if organization:
            return organization

    return ""


def normalize_patentsview_record(record: Dict[str, Any], keyword: str) -> Optional[Dict[str, str]]:
    publication_number = str(record.get("patent_id") or "").strip()
    title = (record.get("patent_title") or "").strip()
    abstract = (record.get("patent_abstract") or "").strip()

    if not publication_number or not title:
        return None

    inventor_names = _build_inventor_names(record)
    assignee = _build_assignee_name(record)

    return {
        "title": title,
        "publication_number": publication_number,
        "technology_domain": infer_technology_domain(keyword, title, abstract),
        "abstract": abstract,
        "assignee": assignee,
        "inventor_names": inventor_names,
        "source": "PatentsView",
    }


def fetch_patentsview_patents(keyword: str, limit: int = DEFAULT_SYNC_LIMIT) -> Tuple[List[Dict[str, str]], Optional[str]]:
    if not _has_real_patentsview_key():
        return [], "PATENTSVIEW_API_KEY is not configured with a real API key"

    keyword_terms = " ".join((keyword or "").strip().split())

    params = {
        "q": json.dumps(
            {
                "_or": [
                    {"_text_phrase": {"patent_title": keyword_terms}},
                    {"_text_phrase": {"patent_abstract": keyword_terms}},
                    {"_text_any": {"patent_title": keyword_terms}},
                    {"_text_any": {"patent_abstract": keyword_terms}},
                ]
            }
        ),
        "f": json.dumps(
            [
                "patent_id",
                "patent_title",
                "patent_abstract",
                "inventors.inventor_name_first",
                "inventors.inventor_name_last",
                "assignees.assignee_organization",
            ]
        ),
        "s": json.dumps([{"patent_id": "desc"}]),
        "o": json.dumps({"size": limit}),
    }
    headers = {
        "X-Api-Key": PATENTSVIEW_API_KEY,
        "Accept": "application/json",
    }

    response = requests.get(
        PATENTSVIEW_API_URL,
        params=params,
        headers=headers,
        timeout=20,
    )
    response.raise_for_status()

    payload = response.json()
    patents: List[Dict[str, str]] = []

    for record in _extract_api_records(payload):
        normalized = normalize_patentsview_record(record, keyword)
        if normalized:
            patents.append(normalized)

    return patents, None


def fetch_external_patents(keyword: str, limit: int = DEFAULT_SYNC_LIMIT) -> Tuple[List[Dict[str, str]], List[str]]:
    errors: List[str] = []

    try:
        patents, config_error = fetch_patentsview_patents(keyword, limit=limit)
        if config_error:
            errors.append(config_error)
        return patents, errors
    except requests.RequestException as exc:
        errors.append(f"PatentsView request failed: {exc}")
    except ValueError as exc:
        errors.append(f"PatentsView response parsing failed: {exc}")

    return [], errors


def ingest_external_patents(keyword: str, limit: int = DEFAULT_SYNC_LIMIT) -> Dict[str, Any]:
    patents, errors = fetch_external_patents(keyword, limit=limit)

    inserted_count = 0
    skipped_count = 0
    inventor_count = 0
    linked_count = 0

    for patent in patents:
        patent_id, was_inserted = save_patent(
            title=patent["title"],
            publication_number=patent["publication_number"],
            technology_domain=patent["technology_domain"],
            abstract=patent["abstract"],
            source=patent["source"],
            assignee=patent["assignee"],
            inventor_names=patent["inventor_names"],
        )

        if was_inserted:
            inserted_count += 1
        else:
            skipped_count += 1

        if not patent["inventor_names"]:
            continue

        inventors = [name.strip() for name in patent["inventor_names"].split(",") if name.strip()]

        for inventor_name in inventors:
            inventor_id = get_or_create_inventor(inventor_name)
            inventor_count += 1

            if inventor_id and link_patent_to_inventor(patent_id, inventor_id):
                linked_count += 1

    return {
        "inserted_count": inserted_count,
        "skipped_count": skipped_count,
        "inventor_names_processed": inventor_count,
        "inventor_links_created": linked_count,
        "fetched_count": len(patents),
        "errors": errors,
    }


def sync_patents_for_keyword(keyword: str, limit: int = DEFAULT_SYNC_LIMIT) -> Dict[str, Any]:
    cleaned_keyword = (keyword or "").strip()

    if not cleaned_keyword:
        return {
            "keyword": "",
            "message": "Keyword is required.",
            "local_matches": [],
            "local_match_count": 0,
            "inserted_count": 0,
            "skipped_count": 0,
            "inventor_names_processed": 0,
            "inventor_links_created": 0,
            "fetched_count": 0,
            "errors": ["Keyword is required"],
        }

    local_matches_before = search_local_patents(cleaned_keyword)
    ingest_result = ingest_external_patents(cleaned_keyword, limit=limit)
    local_matches_after = search_local_patents(cleaned_keyword)

    has_live_matches = ingest_result["fetched_count"] > 0
    live_import_enabled = _has_real_patentsview_key()

    return {
        "keyword": cleaned_keyword,
        "message": (
            f"Loaded {len(local_matches_after)} NJIT database matches for '{cleaned_keyword}'. "
            f"Fetched {ingest_result['fetched_count']} internet patents, "
            f"inserted {ingest_result['inserted_count']}, and skipped {ingest_result['skipped_count']} duplicates."
        ),
        "live_import_enabled": live_import_enabled,
        "has_live_matches": has_live_matches,
        "local_matches_before_count": len(local_matches_before),
        "local_match_count": len(local_matches_after),
        "local_matches": local_matches_after,
        **ingest_result,
    }


def ingest_uspto_data(keyword: str) -> Dict[str, Any]:
    return sync_patents_for_keyword(keyword)
