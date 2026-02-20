from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import User
from analytics.nutrition_aggregator import NutritionAggregator
from datetime import datetime, timedelta

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)

@router.get("/nutrition")
async def get_nutrition_analytics(
    days: int = Query(7),
    current_user: User = Depends(get_current_user)
):
    # Generates mock nutrition data based on days
    daily_data = []
    base_date = datetime.now()
    
    for i in range(days):
        date = base_date - timedelta(days=days-1-i)
        daily_data.append({
            "day": date.strftime("%Y-%m-%d"),
            "day_name": date.strftime("%a"),
            "calories": random.randint(1800, 2400),
            "protein": random.randint(50, 100),
            "carbs": random.randint(200, 300),
            "fat": random.randint(40, 80),
            "sugar": random.randint(30, 60),
            "sodium": random.randint(1500, 2500)
        })
    
    return {
        "daily_data": daily_data,
        "limits": {
            "calories": 2000,
            "sugar": 50,
            "sodium": 2300,
            "protein": 60,
            "carbs": 250,
            "fat": 70
        },
        "macro_distribution": {
            "protein": 25,
            "carbs": 50,
            "fat": 25
        }
    }

@router.get("/risk")
async def get_health_risks(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    escalation_data = NutritionAggregator.check_risk_escalation(db, current_user.id)
    
    risks = []
    if escalation_data["escalated"]:
        for warning in escalation_data["warnings"]:
            risks.append({
                "name": "Health Alert",
                "risk_score": 85,
                "trend": "up",
                "message": warning
            })
    else:
        risks.append({
            "name": "General Health",
            "risk_score": 15,
            "trend": "stable",
            "message": "Metrics look stable. Keep up the good work."
        })
        
    return risks

@router.get("/prediction")
async def get_health_predictions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    escalation_data = NutritionAggregator.check_risk_escalation(db, current_user.id)
    predictions = []
    
    if escalation_data["escalated"]:
        predictions.append({
            "id": "PRED-001",
            "type": "warning",
            "title": "Dietary Limit Breached",
            "description": " ".join(escalation_data["warnings"]),
            "suggestion": "We recommend reviewing your recent orders and selecting 'Low Score' safe alternatives.",
            "intensity": 85
        })
    else:
         predictions.append({
            "id": "PRED-002",
            "type": "success",
            "title": "Nutrition Goals on Track",
            "description": "Your recent dietary metrics align perfectly with your health profile.",
            "suggestion": "Keep favoring Low GI and High Protein foods!",
            "intensity": 90
        })
    return predictions

@router.get("/timeline")
async def get_health_timeline(current_user: User = Depends(get_current_user)):
    base_date = datetime.now()
    timeline = []
    for i in range(10):
        date = base_date - timedelta(days=i*2)
        timeline.append({
            "date": date.strftime("%b %d"),
            "score": random.randint(75, 95),
            "event": "Profile Updated" if i == 9 else ("High Sodium Day" if i % 3 == 0 else "Optimal Nutrition")
        })
    return timeline[::-1]
