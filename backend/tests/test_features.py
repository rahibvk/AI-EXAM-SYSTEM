from app.core.security import verify_password, get_password_hash
from app.services.plagiarism_service import PlagiarismService
from app.utils.analytics import calculate_grade_distribution, calculate_average

# ==========================================
# Feature 1: Security Testing (3 Cases)
# ==========================================

def test_security_hashing_integrity():
    """Case 1: Ensure hashing transforms the input."""
    password = "secure_password_123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert len(hashed) > 0

def test_security_verification_success():
    """Case 2: Ensure correct password verifies successfully."""
    password = "my_secret_key"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed) is True

def test_security_verification_failure():
    """Case 3: Ensure wrong password fails verification."""
    password = "correct_password"
    hashed = get_password_hash(password)
    assert verify_password("wrong_password", hashed) is False


# ==========================================
# Feature 2: Plagiarism Testing (3 Cases)
# ==========================================

def test_plagiarism_identity_match():
    """Case 1: Identical text should have 1.0 similarity."""
    text = "The mitochondria is the powerhouse of the cell."
    assert PlagiarismService.calculate_similarity(text, text) == 1.0

def test_plagiarism_partial_match():
    """Case 2: Similar text should have high similarity."""
    text1 = "The mitochondria is the powerhouse of the cell."
    text2 = "Mitochondria is the powerhouse of the cell." # missing "The"
    similarity = PlagiarismService.calculate_similarity(text1, text2)
    assert similarity > 0.8

def test_plagiarism_no_match():
    """Case 3: Different text should have low similarity."""
    text1 = "Photosynthesis requires sunlight."
    text2 = "The French Revolution began in 1789."
    similarity = PlagiarismService.calculate_similarity(text1, text2)
    assert similarity < 0.4


# ==========================================
# Feature 3: Analytics Testing (3 Cases)
# ==========================================

def test_analytics_grade_distribution():
    """Case 1: Verify correct bucketing of A, B, C, D, F."""
    scores = [95, 85, 75, 65, 55] 
    dist = calculate_grade_distribution(scores)
    assert dist["A"] == 1
    assert dist["B"] == 1
    assert dist["C"] == 1
    assert dist["D"] == 1
    assert dist["F"] == 1

def test_analytics_average_calculation():
    """Case 2: Verify average calculation validity."""
    scores = [100, 50]
    avg = calculate_average(scores)
    assert avg == 75.0

def test_analytics_empty_input():
    """Case 3: Handle empty input gracefully."""
    scores = []
    avg = calculate_average(scores)
    assert avg == 0.0
    dist = calculate_grade_distribution(scores)
    assert dist["A"] == 0
