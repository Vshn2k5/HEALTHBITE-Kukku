from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from models import User, HealthProfile, DailyLog
from schemas import HealthProfileCreate, HealthProfileResponse, DailyLogCreate, DailyLogResponse, HealthStep1, HealthStep2, HealthReportResponse
from database import get_db
from dependencies import get_current_user, check_rate_limit
import json
import random
from datetime import datetime

router = APIRouter(
    prefix="/api/health",
    tags=["health profiles"]
)

from services.risk_engine import get_bmi_category, calculate_status, calculate_overall_risk

@router.post("/profile", response_model=dict)
def create_health_profile(
    profile: HealthProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limit_check: bool = Depends(check_rate_limit)
):
    # Legacy support if needed, but redirects to multi-step logic internally
    height_m = profile.height_cm / 100
    bmi = profile.weight_kg / (height_m * height_m)
    
    db_profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not db_profile:
        db_profile = HealthProfile(user_id=current_user.id)
        db.add(db_profile)
    
    db_profile.age = profile.age
    db_profile.height_cm = profile.height_cm
    db_profile.weight_kg = profile.weight_kg
    db_profile.gender = profile.gender
    db_profile.dietary_preference = profile.dietary_preference
    db_profile.bmi = bmi
    db_profile.bmi_category = get_bmi_category(bmi)
    db_profile.disease = json.dumps(profile.disease)
    db_profile.severity = json.dumps(profile.severity)
    db_profile.health_values = json.dumps(profile.health_values)
    db_profile.allergies = json.dumps(profile.allergies)
    
    db_profile.diabetes_status = calculate_status("diabetes", profile.health_values.get("diabetes", 0))
    db_profile.bp_status = calculate_status("hypertension", profile.health_values.get("hypertension", 0))
    
    score, level = calculate_overall_risk(db_profile)
    db_profile.risk_score = score
    db_profile.risk_level = level
    
    current_user.profile_completed = 1
    current_user.onboarding_step = 3
    db.commit()
    return format_health_profile(db_profile, current_user.name)

@router.get("/profile", response_model=dict)
def get_health_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Health profile not found")
    return format_health_profile(profile, current_user.name)

@router.get("/check", response_model=dict)
def check_health_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    return {
        "has_profile": profile is not None and current_user.profile_completed == 1,
        "onboarding_step": current_user.onboarding_step,
        "user_id": current_user.id,
        "name": current_user.name
    }

@router.post("/step1")
def save_step1(
    data: HealthStep1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limit_check: bool = Depends(check_rate_limit)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    height_m = data.height_cm / 100
    bmi = data.weight_kg / (height_m * height_m)
    bmi_cat = get_bmi_category(bmi)

    if not profile:
        profile = HealthProfile(user_id=current_user.id)
        db.add(profile)
    
    profile.age = data.age
    profile.gender = data.gender
    profile.weight_kg = data.weight_kg
    profile.height_cm = data.height_cm
    profile.bmi = bmi
    profile.bmi_category = bmi_cat
    profile.dietary_preference = data.dietary_preference
    
    current_user.onboarding_step = 1
    db.commit()
    return {"message": "Step 1 saved", "bmi": bmi, "bmi_category": bmi_cat}

@router.post("/step2")
def save_step2(
    data: HealthStep2,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rate_limit_check: bool = Depends(check_rate_limit)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Complete Step 1 first")
    
    profile.disease = json.dumps(data.disease)
    profile.severity = json.dumps(data.severity)
    profile.health_values = json.dumps(data.health_values)
    profile.allergies = json.dumps(data.allergies)
    
    profile.diabetes_status = calculate_status("diabetes", data.health_values.get("diabetes", 0))
    profile.bp_status = calculate_status("hypertension", data.health_values.get("hypertension", 0))
    
    current_user.onboarding_step = 2
    db.commit()
    return {"message": "Step 2 saved"}

@router.post("/finalize")
def finalize_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not initiated")
    
    score, level = calculate_overall_risk(profile)
    profile.risk_score = score
    profile.risk_level = level
    
    current_user.profile_completed = 1
    current_user.onboarding_step = 3
    db.commit()
    return {"message": "Profile finalized", "risk_score": score, "risk_level": level}

@router.get("/report", response_model=HealthReportResponse)
def get_health_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == current_user.id).first()
    if not profile or current_user.profile_completed == 0:
        raise HTTPException(status_code=404, detail="Completed profile not found")

    try:
        diseases = json.loads(profile.disease) if profile.disease else []
        allergies = json.loads(profile.allergies) if profile.allergies and profile.allergies != "None" else []
    except json.JSONDecodeError as e:
        print(f"Error parsing report data JSON: {e}")
        diseases = []
        allergies = []
    except Exception as e:
        print(f"Unexpected error loading report data: {e}")
        diseases = []
        allergies = []

    recs = ["Stay hydrated with 3L water daily.", "Maintain a regular sleep cycle."]
    if "Diabetes" in [d.capitalize() for d in diseases]:
        recs.append("Focus on low-GI complex carbohydrates.")
        recs.append("Restrict added sugars and sugary beverages.")
    if "Hypertension" in [d.capitalize() for d in diseases]:
        recs.append("Reduce sodium intake to less than 2300mg/day.")
    if profile.bmi_category in ["Obese", "Overweight"]:
        recs.append("Incorporate 30 mins of moderate cardio daily.")
    if not diseases:
        recs.append("Keep up the balanced diet to prevent future risks.")

    return {
        "age": profile.age,
        "gender": profile.gender,
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "bmi": profile.bmi,
        "bmi_category": profile.bmi_category or "Normal",
        "disease": diseases,
        "allergies": allergies,
        "risk_score": profile.risk_score or 0,
        "risk_level": profile.risk_level or "Low",
        "recommendations": recs
    }

@router.post("/daily-log")
def create_daily_log(
    log: DailyLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.now().strftime("%Y-%m-%d")
    db_log = db.query(DailyLog).filter(DailyLog.user_id == current_user.id, DailyLog.date == today).first()
    if db_log:
        if log.water_intake_ml: db_log.water_intake_ml += log.water_intake_ml
        if log.steps: db_log.steps = log.steps
        if log.mood: db_log.mood = log.mood
    else:
        db_log = DailyLog(user_id=current_user.id, **log.dict())
        db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.get("/daily-log")
def get_daily_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.now().strftime("%Y-%m-%d")
    log = db.query(DailyLog).filter(DailyLog.user_id == current_user.id, DailyLog.date == today).first()
    return log or {"water_intake_ml": 0, "steps": 0, "mood": "Neutral"}

def format_health_profile(profile, user_name="User"):
    """Convert database profile to response format with JSON parsing"""
    try:
        disease_list = json.loads(profile.disease) if profile.disease else []
        severity_dict = json.loads(profile.severity) if profile.severity else {}
        health_values_dict = json.loads(profile.health_values) if profile.health_values else {}
        allergies_list = json.loads(profile.allergies) if profile.allergies and profile.allergies != "None" else []
    except (json.JSONDecodeError, TypeError):
        disease_list = []
        severity_dict = {}
        health_values_dict = {}
        allergies_list = []
    
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "name": user_name,
        "age": profile.age,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "bmi": profile.bmi,
        "gender": profile.gender,
        "dietary_preference": profile.dietary_preference,
        "disease": disease_list,
        "severity": severity_dict,
        "health_values": health_values_dict,
        "diabetes_status": profile.diabetes_status,
        "bp_status": profile.bp_status,
        "cholesterol_status": profile.cholesterol_status,
        "bmi_category": profile.bmi_category or get_bmi_category(profile.bmi or 0),
        "risk_score": profile.risk_score or 0,
        "risk_level": profile.risk_level or "Low",
        "allergies": allergies_list
    }
