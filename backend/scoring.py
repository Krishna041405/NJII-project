def calculate_fit_score(patent_count, technology_domains):
    score = 5.0

    # Patent count score
    if patent_count >= 3:
        score += 4.0
    elif patent_count == 2:
        score += 3.0
    elif patent_count == 1:
        score += 2.0

    # Technology domain bonus
    for domain in technology_domains:
        domain_lower = domain.lower()

        if "ai" in domain_lower or "ml" in domain_lower:
            score += 1.5
        elif "manufacturing" in domain_lower:
            score += 1.0
        elif "health" in domain_lower:
            score += 1.2

    # cap score at 10
    if score > 10:
        score = 10.0

    return round(score, 2)