def calculate_score(total_score: int, num_users_scored: int) -> float:
    score = 0
    if num_users_scored:
        score = total_score / num_users_scored

    return round(score, 1)


def calculate_slope(new_score: float, old_score: float) -> float:
    slope = 0
    if old_score:
        slope = new_score - old_score

    return round(slope, 2)
