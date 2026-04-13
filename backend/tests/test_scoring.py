from scoring import calculate_fit_score


def test_calculate_fit_score_caps_at_ten():
    score = calculate_fit_score(3, ["AI/ML", "Health"])

    assert score == 10.0


def test_calculate_fit_score_for_single_health_patent():
    score = calculate_fit_score(1, ["Health"])

    assert score == 8.2
