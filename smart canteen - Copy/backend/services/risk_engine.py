import json
from config.severity_weights import SEVERITY_WEIGHTS

def get_bmi_category(bmi):
    if bmi < 18.5: return "Underweight"
    if 18.5 <= bmi < 25: return "Normal"
    if 25 <= bmi < 30: return "Overweight"
    return "Obese"

def calculate_status(condition, value):
    """Rule-based threshold logic for health status classification"""
    if not value or value == 0:
        return "Normal"
    
    try:
        if condition == "diabetes":
            val = float(value)
            if val < 100: return "Normal"
            if 100 <= val <= 125: return "Elevated"
            return "High"
            
        if condition == "hypertension":
            if isinstance(value, str) and "/" in value:
                systolic = float(value.split("/")[0])
            else:
                systolic = float(value)
            
            if systolic < 120: return "Normal"
            if 120 <= systolic <= 139: return "Elevated"
            return "Critical"

        if condition == "cholesterol":
            val = float(value)
            if val < 130: return "Normal"
            if 130 <= val <= 159: return "Elevated"
            return "High"
    except (ValueError, TypeError, IndexError):
        pass
    return "Normal"

def calculate_overall_risk(profile):
    """
    Calculate a normalized risk score (0-100) and category.
    Formula: Risk Score = (BMI * 0.25) + (Disease * 0.40) + (Dietary_Habit * 0.20) + (Allergy * 0.15)
    """
    # 1. BMI Risk (0-100 scale, weighted 25%)
    bmi_risk_val = 0
    if profile.bmi >= 30: bmi_risk_val = 100 # Obese
    elif profile.bmi >= 25: bmi_risk_val = 60 # Overweight
    elif profile.bmi < 18.5: bmi_risk_val = 50 # Underweight
    else: bmi_risk_val = 0 # Normal
    
    bmi_risk_score = bmi_risk_val * 0.25
    
    # 2. Disease Risk (0-100 scale, weighted 40%)
    # Contribution from sugar (diabetes), sodium (hypertension), saturated fat (cholesterol)
    disease_base_score = 0
    try:
        severity_dict = json.loads(profile.severity) if profile.severity else {}
    except (json.JSONDecodeError, TypeError):
        severity_dict = {}

    if profile.diabetes_status == "High": disease_base_score += 40 * SEVERITY_WEIGHTS.get(severity_dict.get("Diabetes", "Moderate"), 1.0)
    elif profile.diabetes_status == "Elevated": disease_base_score += 20 * SEVERITY_WEIGHTS.get(severity_dict.get("Diabetes", "Mild"), 0.5)

    if profile.bp_status == "Critical": disease_base_score += 40 * SEVERITY_WEIGHTS.get(severity_dict.get("Hypertension", "Moderate"), 1.0)
    elif profile.bp_status == "Elevated": disease_base_score += 20 * SEVERITY_WEIGHTS.get(severity_dict.get("Hypertension", "Mild"), 0.5)

    if profile.cholesterol_status == "High": disease_base_score += 20 * SEVERITY_WEIGHTS.get(severity_dict.get("Cholesterol", "Moderate"), 1.0)
    elif profile.cholesterol_status == "Elevated": disease_base_score += 10 * SEVERITY_WEIGHTS.get(severity_dict.get("Cholesterol", "Mild"), 0.5)

    # Cap disease base score at 100
    disease_base_score = min(100, disease_base_score)
    disease_risk_score = disease_base_score * 0.40
    
    # 3. Dietary Habit Risk (0-100 scale, weighted 20%)
    # Assuming baseline risk of 20. This could be enriched later based on DailyLog or recent orders.
    dietary_risk_val = 20
    if profile.dietary_preference == "Non-Veg":
        dietary_risk_val += 10
    dietary_risk_score = dietary_risk_val * 0.20
    
    # 4. Allergy Risk (0-100 scale, weighted 15%)
    allergy_base_score = 0
    try:
        allergies = json.loads(profile.allergies) if profile.allergies and profile.allergies != "None" else []
        if isinstance(allergies, list):
            for a in allergies:
                saf_sev = a.get("severity", "Moderate") if isinstance(a, dict) else "Moderate"
                if saf_sev == "Severe":
                    allergy_base_score += 50
                elif saf_sev == "Moderate":
                    allergy_base_score += 30
                else:
                    allergy_base_score += 10
    except (json.JSONDecodeError, TypeError):
        pass
    
    allergy_base_score = min(100, allergy_base_score)
    allergy_risk_score = allergy_base_score * 0.15

    # Total Risk Score (0-100)
    total_score = bmi_risk_score + disease_risk_score + dietary_risk_score + allergy_risk_score
    total_score = min(100.0, round(total_score, 1))
    
    # Risk categories
    if total_score <= 30:
        level = "Low"
    elif total_score <= 60:
        level = "Moderate"
    else:
        level = "High"
        
    return total_score, level
