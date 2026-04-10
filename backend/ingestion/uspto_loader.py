import requests
import mysql.connector


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Kamit934600.",
        database="patent_system"
    )

def get_or_create_inventor(full_name):
    db = get_db_connection()
    cursor = db.cursor()

    full_name = full_name.strip()
    name_parts = full_name.split()

    if len(name_parts) == 1:
        first_name = name_parts[0]
        last_name = ""
    else:
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])

    check_query = """
    SELECT inventor_id
    FROM inventors
    WHERE first_name = %s AND last_name = %s
    """
    cursor.execute(check_query, (first_name, last_name))
    existing = cursor.fetchone()

    if existing:
        inventor_id = existing[0]
    else:
        insert_query = """
        INSERT INTO inventors (first_name, last_name, affiliation, email)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (first_name, last_name, "Imported USPTO", ""))
        db.commit()
        inventor_id = cursor.lastrowid

    cursor.close()
    db.close()
    return inventor_id

def link_patent_to_inventor(patent_id, inventor_id):
    db = get_db_connection()
    cursor = db.cursor()

    check_query = """
    SELECT *
    FROM patent_inventors
    WHERE patent_id = %s AND inventor_id = %s
    """
    cursor.execute(check_query, (patent_id, inventor_id))
    existing = cursor.fetchone()

    if not existing:
        insert_query = """
        INSERT INTO patent_inventors (patent_id, inventor_id)
        VALUES (%s, %s)
        """
        cursor.execute(insert_query, (patent_id, inventor_id))
        db.commit()

    cursor.close()
    db.close()


def save_patent(title, publication_number, technology_domain, abstract="", source="USPTO", assignee="", inventor_names=""):
    db = get_db_connection()
    cursor = db.cursor()

    # Check if patent already exists
    check_query = "SELECT patent_id FROM patents WHERE publication_number = %s"
    cursor.execute(check_query, (publication_number,))
    existing_patent = cursor.fetchone()

    if existing_patent:
        patent_id = existing_patent[0]
        cursor.close()
        db.close()
        return patent_id, False

    query = """
    INSERT INTO patents (
        title,
        patent_number,
        technology_domain,
        abstract,
        source,
        assignee,
        publication_number,
        inventor_names
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (
        title,
        publication_number,
        technology_domain,
        abstract,
        source,
        assignee,
        publication_number,
        inventor_names
    ))

    db.commit()
    patent_id = cursor.lastrowid

    cursor.close()
    db.close()

    return patent_id, True


def fetch_uspto_patents(keyword):
    print(f"Fetching patents for keyword: {keyword}")

    sample_data = [
        {
            "title": f"{keyword} Medical Device",
            "publication_number": "US202500001",
            "technology_domain": "AI/ML",
            "abstract": "A sample AI medical patent.",
            "assignee": "Sample Health Tech",
            "inventor_names": "John Doe, Jane Smith"
        },
        {
            "title": f"{keyword} Manufacturing Control System",
            "publication_number": "US202500002",
            "technology_domain": "Manufacturing",
            "abstract": "A sample manufacturing patent.",
            "assignee": "Sample Manufacturing Inc",
            "inventor_names": "Alice Brown, Bob Green"
        }
    ]

    return sample_data


def ingest_uspto_data(keyword):
    patents = fetch_uspto_patents(keyword)

    inserted_count = 0
    skipped_count = 0
    inventor_count = 0

    for patent in patents:
        patent_id, was_inserted = save_patent(
            title=patent["title"],
            publication_number=patent["publication_number"],
            technology_domain=patent["technology_domain"],
            abstract=patent["abstract"],
            assignee=patent["assignee"],
            inventor_names=patent["inventor_names"]
        )

        if was_inserted:
            inserted_count += 1
        else:
            skipped_count += 1

        inventors = patent["inventor_names"].split(",")

        for inventor_name in inventors:
            inventor_id = get_or_create_inventor(inventor_name)
            link_patent_to_inventor(patent_id, inventor_id)
            inventor_count += 1

    return {
        "message": f"Inserted {inserted_count} patents, skipped {skipped_count} duplicates, processed {inventor_count} inventor links for keyword '{keyword}'",
        "inserted_count": inserted_count,
        "skipped_count": skipped_count,
        "inventor_links_processed": inventor_count
    }