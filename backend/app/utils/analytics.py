from typing import List, Dict

def calculate_grade_distribution(scores: List[float]) -> Dict[str, int]:
    """
    Calculates the distribution of grades (A, B, C, D, F) from a list of scores.
    Assumes scores are out of 100.
    """
    distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
    
    for score in scores:
        if score >= 90:
            distribution["A"] += 1
        elif score >= 80:
            distribution["B"] += 1
        elif score >= 70:
            distribution["C"] += 1
        elif score >= 60:
            distribution["D"] += 1
        else:
            distribution["F"] += 1
            
    return distribution

def calculate_average(scores: List[float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)
