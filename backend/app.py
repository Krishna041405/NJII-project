from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import get_db_connection
from scoring import calculate_fit_score
from ingestion.uspto_loader import ingest_uspto_data

app = FastAPI(title="NJII Patent Matching API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API is running"}


@app.get("/inventors")
def get_inventors():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM inventors")
    inventors = cursor.fetchall()

    cursor.close()
    db.close()

    return inventors


@app.get("/patents")
def get_patents():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT * FROM patents")
    patents = cursor.fetchall()

    cursor.close()
    db.close()

    return patents

@app.get("/search")
def search_patents(keyword: str):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT * FROM patents
    WHERE title LIKE %s OR technology_domain LIKE %s
    """
    search_value = f"%{keyword}%"

    cursor.execute(query, (search_value, search_value))
    results = cursor.fetchall()

    cursor.close()
    db.close()

    return results

@app.get("/filter")
def filter_patents(domain: str):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    if domain == "All":
        cursor.execute("SELECT * FROM patents")
    else:
        query = "SELECT * FROM patents WHERE technology_domain = %s"
        cursor.execute(query, (domain,))

    patents = cursor.fetchall()

    cursor.close()
    db.close()

    return patents

@app.get("/ranked-inventors")
def get_ranked_inventors():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT 
        i.inventor_id,
        i.first_name,
        i.last_name,
        COUNT(pi.patent_id) AS patent_count,
        GROUP_CONCAT(p.technology_domain) AS technology_domains
    FROM inventors i
    LEFT JOIN patent_inventors pi ON i.inventor_id = pi.inventor_id
    LEFT JOIN patents p ON pi.patent_id = p.patent_id
    GROUP BY i.inventor_id, i.first_name, i.last_name
    """

    cursor.execute(query)
    inventors = cursor.fetchall()

    results = []

    for inventor in inventors:
        patent_count = inventor["patent_count"]

        if inventor["technology_domains"]:
            technology_domains = inventor["technology_domains"].split(",")
        else:
            technology_domains = []

        fit_score = calculate_fit_score(patent_count, technology_domains)

        results.append({
            "inventor_id": inventor["inventor_id"],
            "inventor_name": f"{inventor['first_name']} {inventor['last_name']}",
            "patent_count": patent_count,
            "technology_domains": technology_domains,
            "fit_score": fit_score
        })

    cursor.close()
    db.close()

    results.sort(key=lambda x: x["fit_score"], reverse=True)
    return results

@app.get("/discover-inventors")
def discover_inventors(keyword: str):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    query = """
    SELECT DISTINCT
        i.inventor_id,
        i.first_name,
        i.last_name,
        i.affiliation,
        i.email,
        p.title AS patent_title,
        p.technology_domain
    FROM patents p
    JOIN patent_inventors pi ON p.patent_id = pi.patent_id
    JOIN inventors i ON pi.inventor_id = i.inventor_id
    WHERE p.title LIKE %s OR p.technology_domain LIKE %s
    """

    search_value = f"%{keyword}%"
    cursor.execute(query, (search_value, search_value))
    results = cursor.fetchall()

    cursor.close()
    db.close()

    return results

@app.post("/ingest-uspto")
def ingest_uspto(keyword: str):
    result = ingest_uspto_data(keyword)
    return result