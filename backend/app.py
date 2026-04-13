from typing import Any, Callable

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import (
    discover_inventors_by_keyword,
    filter_patents_by_domain,
    get_ranked_inventors_data,
    list_inventors,
    list_patents,
)
from scoring import calculate_fit_score
from ingestion.uspto_loader import ingest_uspto_data, search_local_patents, sync_patents_for_keyword

app = FastAPI(title="NJII Patent Matching API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _run_backend_call(operation: Callable[[], Any], service_name: str) -> Any:
    try:
        return operation()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=f"{service_name} is not configured: {exc}") from exc
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503,
            detail=f"{service_name} is unavailable. Check Supabase connectivity and credentials.",
        ) from exc


@app.get("/")
def home():
    return {"message": "API is running"}


@app.get("/inventors")
def get_inventors():
    return _run_backend_call(list_inventors, "Inventor data service")


@app.get("/patents")
def get_patents():
    return _run_backend_call(list_patents, "Patent data service")

@app.get("/search")
def search_patents(keyword: str, auto_sync: bool = True):
    if auto_sync:
        return _run_backend_call(lambda: sync_patents_for_keyword(keyword), "Patent sync service")

    return _run_backend_call(lambda: search_local_patents(keyword), "Patent search service")

@app.get("/filter")
def filter_patents(domain: str):
    return _run_backend_call(lambda: filter_patents_by_domain(domain), "Patent filter service")

@app.get("/ranked-inventors")
def get_ranked_inventors():
    inventors = _run_backend_call(get_ranked_inventors_data, "Inventor ranking service")
    results = []

    for inventor in inventors:
        patent_count = inventor["patent_count"]
        technology_domains = inventor["technology_domains"] or []

        fit_score = calculate_fit_score(patent_count, technology_domains)

        results.append({
            "inventor_id": inventor["inventor_id"],
            "inventor_name": f"{inventor['first_name']} {inventor['last_name']}",
            "patent_count": patent_count,
            "technology_domains": technology_domains,
            "fit_score": fit_score
        })

    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return results

@app.get("/discover-inventors")
def discover_inventors(keyword: str):
    return _run_backend_call(lambda: discover_inventors_by_keyword(keyword), "Inventor discovery service")

@app.post("/ingest-uspto")
def ingest_uspto(keyword: str):
    result = _run_backend_call(lambda: ingest_uspto_data(keyword), "USPTO ingestion service")
    return result


@app.post("/sync-patents")
def sync_patents(keyword: str):
    return _run_backend_call(lambda: sync_patents_for_keyword(keyword), "Patent sync service")
