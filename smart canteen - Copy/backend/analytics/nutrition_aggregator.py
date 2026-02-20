from sqlalchemy import func
from datetime import datetime, timedelta
from models import Order, HealthProfile

class NutritionAggregator:
    @staticmethod
    def get_daily_nutrition(db, user_id, date_str=None):
        """
        Calculates the sum of calories and sugar from all orders placed on a specific date.
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
            
        daily_orders = db.query(Order).filter(
            Order.user_id == user_id,
            Order.created_at.startswith(date_str)
        ).all()
        
        total_calories = sum(order.total_calories or 0 for order in daily_orders)
        total_sugar = sum(order.total_sugar or 0 for order in daily_orders)
        
        return {
            "date": date_str,
            "total_calories": total_calories,
            "total_sugar": total_sugar,
            "order_count": len(daily_orders)
        }

    @staticmethod
    def get_weekly_sodium_trend(db, user_id):
        """
        Calculates the 7-day rolling average for sodium intake.
        """
        today = datetime.now()
        seven_days_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # In SQLite, we can just fetch the past 7 days and aggregate in Python or via SQLAlchemy
        past_week_orders = db.query(Order).filter(
            Order.user_id == user_id,
            Order.created_at >= seven_days_ago
        ).all()
        
        # Group by date
        daily_sodium = {}
        for order in past_week_orders:
            date_key = order.created_at[:10]  # Extract YYYY-MM-DD
            daily_sodium[date_key] = daily_sodium.get(date_key, 0) + (order.total_sodium or 0)
            
        # Calculate Rolling 7-day average
        days_with_data = len(daily_sodium)
        total_weekly_sodium = sum(daily_sodium.values())
        avg_sodium = total_weekly_sodium / days_with_data if days_with_data > 0 else 0
        
        return {
            "7_day_average": avg_sodium,
            "daily_breakdown": daily_sodium
        }

    @staticmethod
    def check_risk_escalation(db, user_id):
        """
        Analyzes recent consumption against thresholds to check for risk escalation.
        """
        nutrition = NutritionAggregator.get_daily_nutrition(db, user_id)
        sodium_trend = NutritionAggregator.get_weekly_sodium_trend(db, user_id)
        
        profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
        if not profile:
            return {"escalated": False, "warnings": []}
            
        warnings = []
        is_escalated = False
        
        # Escalation Logic 1: Excessive Daily Calories for Obese/Overweight
        if profile.bmi_category in ["Obese", "Overweight"] and nutrition["total_calories"] > 2500:
            warnings.append("Daily calorie intake significantly exceeds target for weight management.")
            is_escalated = True
            
        # Escalation Logic 2: Excessive Sugar for Diabetics
        if profile.diabetes_status in ["High", "Elevated"] and nutrition["total_sugar"] > 50:
            warnings.append("Daily sugar intake is dangerously high for diabetic profile.")
            is_escalated = True
            
        # Escalation Logic 3: Excessive 7-day average sodium for Hypertension
        if profile.bp_status in ["Critical", "Elevated"] and sodium_trend["7_day_average"] > 2300:
            warnings.append(f"7-day average sodium ({sodium_trend['7_day_average']:.0f}mg) exceeds hypertension limits.")
            is_escalated = True
            
        return {
            "escalated": is_escalated,
            "warnings": warnings,
            "current_metrics": {
                "daily_calories": nutrition["total_calories"],
                "daily_sugar": nutrition["total_sugar"],
                "weekly_avg_sodium": sodium_trend["7_day_average"]
            }
        }
