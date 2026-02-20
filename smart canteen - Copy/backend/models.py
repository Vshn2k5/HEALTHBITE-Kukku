from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="USER")
    disabled = Column(Integer, default=0)
    profile_completed = Column(Integer, default=0) # 0 = false, 1 = true
    onboarding_step = Column(Integer, default=0)

    health_profile = relationship("HealthProfile", back_populates="user", uselist=False)
    orders = relationship("Order", back_populates="user")
    daily_logs = relationship("DailyLog", back_populates="user")


class HealthProfile(Base):
    __tablename__ = "health_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    age = Column(Integer)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    bmi = Column(Float)
    gender = Column(String)

    # Health conditions as JSON or explicit flags
    disease = Column(String, default="[]")  # List of names like ["Diabetes", "Anemia"]
    severity = Column(String, default="{}") # JSON storing severity for each condition
    health_values = Column(String, default="{}") # JSON storing numeric values (sugar, bp)

    # Detailed status computed based on rules
    diabetes_status = Column(String, default="Normal")
    bp_status = Column(String, default="Normal")
    cholesterol_status = Column(String, default="Normal")
    
    bmi_category = Column(String, default="Normal")
    risk_score = Column(Integer, default=0)
    risk_level = Column(String, default="Low")

    # Dietary & Allergies
    allergies = Column(String, default="None")  # JSON list of structured allergies
    dietary_preference = Column(String, default="Veg")

    user = relationship("User", back_populates="health_profile")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    items = Column(String)  # JSON string of food IDs
    total_price = Column(Float)
    total_calories = Column(Float)
    total_sugar = Column(Float)
    total_sodium = Column(Float)
    created_at = Column(String, default=lambda: datetime.now().isoformat())

    user = relationship("User", back_populates="orders")


class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    water_intake_ml = Column(Integer, default=0)
    steps = Column(Integer, default=0)
    mood = Column(String, default="Neutral")

    user = relationship("User", back_populates="daily_logs")

