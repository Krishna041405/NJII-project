import os
from typing import Any, Dict, List, Optional

import requests

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
SUPABASE_AUTH_TOKEN = os.getenv("SUPABASE_AUTH_TOKEN", "").strip()
SUPABASE_SCHEMA = os.getenv("SUPABASE_SCHEMA", "public")


def _require_supabase_config() -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY must be configured.")


def _headers(prefer: Optional[str] = None) -> Dict[str, str]:
    _require_supabase_config()

    headers = {
        "apikey": SUPABASE_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Accept-Profile": SUPABASE_SCHEMA,
        "Content-Profile": SUPABASE_SCHEMA,
    }

    if SUPABASE_AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {SUPABASE_AUTH_TOKEN}"

    if prefer:
        headers["Prefer"] = prefer

    return headers


def _table_url(table: str) -> str:
    _require_supabase_config()
    return f"{SUPABASE_URL}/rest/v1/{table}"


def _request(
    method: str,
    table: str,
    params: Optional[Dict[str, Any]] = None,
    payload: Optional[Any] = None,
    prefer: Optional[str] = None,
) -> Any:
    response = requests.request(
        method,
        _table_url(table),
        headers=_headers(prefer=prefer),
        params=params,
        json=payload,
        timeout=20,
    )
    response.raise_for_status()

    if not response.text:
        return None

    return response.json()


def get_db_connection() -> None:
    return None


def list_inventors() -> List[Dict[str, Any]]:
    return _request("GET", "inventors", params={"select": "*"}) or []


def list_patents() -> List[Dict[str, Any]]:
    return _request("GET", "patents", params={"select": "*", "order": "patent_id.desc"}) or []


def filter_patents_by_domain(domain: str) -> List[Dict[str, Any]]:
    patents = list_patents()

    if domain == "All":
        return patents

    return [patent for patent in patents if patent.get("technology_domain") == domain]


def _matches_keyword(value: Any, keyword: str) -> bool:
    if value is None:
        return False

    return keyword.lower() in str(value).lower()


def search_patents_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    cleaned_keyword = (keyword or "").strip()

    if not cleaned_keyword:
        return []

    patents = list_patents()

    return [
        patent
        for patent in patents
        if any(
            _matches_keyword(patent.get(field_name), cleaned_keyword)
            for field_name in ("title", "technology_domain", "abstract", "inventor_names", "assignee")
        )
    ]


def get_inventor_by_name(first_name: str, last_name: str) -> Optional[Dict[str, Any]]:
    rows = _request(
        "GET",
        "inventors",
        params={
            "select": "*",
            "first_name": f"eq.{first_name}",
            "last_name": f"eq.{last_name}",
            "limit": 1,
        },
    ) or []
    return rows[0] if rows else None


def create_inventor(first_name: str, last_name: str, affiliation: str, email: str = "") -> Dict[str, Any]:
    rows = _request(
        "POST",
        "inventors",
        payload={
            "first_name": first_name,
            "last_name": last_name,
            "affiliation": affiliation,
            "email": email,
        },
        prefer="return=representation",
    ) or []
    return rows[0]


def get_patent_by_publication_number(publication_number: str) -> Optional[Dict[str, Any]]:
    rows = _request(
        "GET",
        "patents",
        params={
            "select": "*",
            "publication_number": f"eq.{publication_number}",
            "limit": 1,
        },
    ) or []
    return rows[0] if rows else None


def create_patent(
    title: str,
    publication_number: str,
    technology_domain: str,
    abstract: str = "",
    source: str = "Internet",
    assignee: str = "",
    inventor_names: str = "",
) -> Dict[str, Any]:
    rows = _request(
        "POST",
        "patents",
        payload={
            "title": title,
            "patent_number": publication_number,
            "technology_domain": technology_domain,
            "abstract": abstract,
            "source": source,
            "assignee": assignee,
            "publication_number": publication_number,
            "inventor_names": inventor_names,
        },
        prefer="return=representation",
    ) or []
    return rows[0]


def get_patent_inventor_link(patent_id: int, inventor_id: int) -> Optional[Dict[str, Any]]:
    rows = _request(
        "GET",
        "patent_inventors",
        params={
            "select": "*",
            "patent_id": f"eq.{patent_id}",
            "inventor_id": f"eq.{inventor_id}",
            "limit": 1,
        },
    ) or []
    return rows[0] if rows else None


def create_patent_inventor_link(patent_id: int, inventor_id: int) -> Dict[str, Any]:
    rows = _request(
        "POST",
        "patent_inventors",
        payload={"patent_id": patent_id, "inventor_id": inventor_id},
        prefer="return=representation",
    ) or []
    return rows[0]


def get_ranked_inventors_data() -> List[Dict[str, Any]]:
    inventors = list_inventors()
    patents = list_patents()
    links = _request("GET", "patent_inventors", params={"select": "*"}) or []

    patents_by_id = {patent["patent_id"]: patent for patent in patents}
    links_by_inventor: Dict[int, List[Dict[str, Any]]] = {}

    for link in links:
        inventor_id = link["inventor_id"]
        links_by_inventor.setdefault(inventor_id, []).append(link)

    results: List[Dict[str, Any]] = []

    for inventor in inventors:
        inventor_links = links_by_inventor.get(inventor["inventor_id"], [])
        inventor_patents = [
            patents_by_id[link["patent_id"]]
            for link in inventor_links
            if link["patent_id"] in patents_by_id
        ]
        technology_domains = [
            patent.get("technology_domain")
            for patent in inventor_patents
            if patent.get("technology_domain")
        ]

        results.append(
            {
                "inventor_id": inventor["inventor_id"],
                "first_name": inventor.get("first_name", ""),
                "last_name": inventor.get("last_name", ""),
                "patent_count": len(inventor_patents),
                "technology_domains": technology_domains,
            }
        )

    return results


def discover_inventors_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    patents = search_patents_by_keyword(keyword)

    if not patents:
        return []

    patent_ids = {patent["patent_id"] for patent in patents}
    links = _request("GET", "patent_inventors", params={"select": "*"}) or []
    matching_links = [link for link in links if link["patent_id"] in patent_ids]

    if not matching_links:
        return []

    inventors = list_inventors()
    inventors_by_id = {inventor["inventor_id"]: inventor for inventor in inventors}
    patents_by_id = {patent["patent_id"]: patent for patent in patents}
    discovered: List[Dict[str, Any]] = []
    seen_pairs = set()

    for link in matching_links:
        inventor = inventors_by_id.get(link["inventor_id"])
        patent = patents_by_id.get(link["patent_id"])

        if not inventor or not patent:
            continue

        pair_key = (inventor["inventor_id"], patent["patent_id"])
        if pair_key in seen_pairs:
            continue

        seen_pairs.add(pair_key)
        discovered.append(
            {
                "inventor_id": inventor["inventor_id"],
                "first_name": inventor.get("first_name", ""),
                "last_name": inventor.get("last_name", ""),
                "affiliation": inventor.get("affiliation", ""),
                "email": inventor.get("email", ""),
                "patent_title": patent.get("title", ""),
                "technology_domain": patent.get("technology_domain", ""),
            }
        )

    return discovered
