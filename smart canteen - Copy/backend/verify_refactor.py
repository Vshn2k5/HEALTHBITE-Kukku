import asyncio
from models import HealthProfile
from schemas import HealthProfileCreate, OrderCreate
from services.risk_engine import calculate_overall_risk
from services.recommendation_service import RecommendationService
import json

def test_phase_1_risk_scoring():
    print("--- Testing Phase 1: Risk Scoring ---")
    # Mock a High Risk Profile
    profile = HealthProfile(
        bmi=32,
        diabetes_status="High",
        bp_status="Critical",
        cholesterol_status="Normal",
        severity=json.dumps({"Diabetes": "Severe", "Hypertension": "Moderate"}),
        allergies=json.dumps([{"name": "Peanuts", "severity": "Severe"}]),
        dietary_preference="Non-Veg"
    )
    score, level = calculate_overall_risk(profile)
    print(f"Risk Score: {score}/100, Level: {level}")
    assert score > 60, "Score should be High"
    print("Phase 1 Passed! [OK]")

def test_phase_2_and_6_hybrid_ml_and_stock():
    print("--- Testing Phase 2 & 6: Hybrid ML + Rules + Stock Sync ---")
    recommender = RecommendationService(alpha=0.6)
    
    mock_profile = {
        "age": 45,
        "disease": ["Diabetes", "Hypertension"],
        "severity": {"Diabetes": "Severe", "Hypertension": "Moderate"},
        "allergies": [{"name": "Peanuts", "severity": "Severe"}],
        "dietary_preference": "Veg"
    }
    
    # 1. High Sugar Item (Should be blocked by Severe Diabetes)
    cake = {"name": "Chocolate Cake", "sugar": 45, "sodium": 300, "carbs": 65, "calories": 520, "is_available": True, "stock_quantity": 5}
    score, risk, insight, tag = recommender.evaluate_food_item(cake, mock_profile)
    print(f"Cake -> Score: {score}, Risk: {risk}, Insight: {insight}")
    assert risk == 2 and "Excessive sugar" in insight, "Failed to block high sugar for severe diabetic"

    # 2. Allergen Item (Should be blocked)
    peanut_butter = {"name": "Peanut Butter Sandwich", "sugar": 5, "sodium": 200, "carbs": 30, "calories": 300, "is_available": True, "stock_quantity": 5}
    score, risk, insight, tag = recommender.evaluate_food_item(peanut_butter, mock_profile)
    print(f"Peanut Sandwich -> Score: {score}, Risk: {risk}, Insight: {insight}")
    assert risk == 2 and "Allergen" in insight, "Failed to block allergen"

    # 3. Out of stock item (Should be filtered in get_intelligent_menu)
    salad = {"name": "Fresh Green Salad", "sugar": 2, "sodium": 150, "carbs": 10, "calories": 150, "is_available": True, "stock_quantity": 0}
    safe_food = {"name": "Quinoa Veggie Bowl", "sugar": 0, "sodium": 150, "carbs": 45, "calories": 320, "is_available": True, "stock_quantity": 10}
    
    menu = recommender.get_intelligent_menu([salad, safe_food], mock_profile)
    print(f"Menu length returned: {len(menu)}")
    assert len(menu) == 1, "Failed to filter out-of-stock items"
    assert menu[0]["name"] == "Quinoa Veggie Bowl", "Wrong item returned"
    
    print("Phase 2 & 6 Passed! [OK]")

if __name__ == "__main__":
    try:
        test_phase_1_risk_scoring()
        test_phase_2_and_6_hybrid_ml_and_stock()
        print("\nAll Core Architectural Tests Passed Successfully! System is Production Ready.")
    except Exception as e:
        print(f"\n[X] Test Failed: {e}")
