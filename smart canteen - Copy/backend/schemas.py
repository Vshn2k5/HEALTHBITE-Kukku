from pydantic import BaseModel, Field, validator
import re
from typing import Optional, List
from enum import Enum


class RoleEnum(str, Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class DiseaseEnum(str, Enum):
    DIABETES = "Diabetes"
    HYPERTENSION = "Hypertension"
    OBESITY = "Obesity"
    ANEMIA = "Anemia"
    HEART_DISEASE = "Heart Disease"
    NONE = "None"


# User schemas
class UserBase(BaseModel):
    name: str
    email: str


class UserCreate(UserBase):
    password: str
    role: RoleEnum


class UserResponse(UserBase):
    id: int
    role: str
    disabled: int

    class Config:
        from_attributes = True


# Auth schemas
class LoginRequest(BaseModel):
    email: str
    password: str
    role: RoleEnum


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class VerifyIdentityRequest(BaseModel):
    email: str
    name: str


class DirectResetPasswordRequest(BaseModel):
    email: str
    new_password: str


class LoginResponse(BaseModel):
    message: str
    email: str
    name: str
    role: str
    token: str
    profile_completed: bool = False
    onboarding_step: int = 0


# Health profile schemas
class HealthProfileBase(BaseModel):
    age: int = Field(..., ge=1, le=120)
    height_cm: float = Field(..., ge=50, le=300)
    weight_kg: float = Field(..., ge=10, le=500)
    gender: str = Field(default="Other")
    disease: List[str] = Field(default=[])
    dietary_preference: str = Field(default="Veg", pattern='^(Veg|Vegan|Non-Veg)$')
    severity: Optional[dict] = Field(default={})
    health_values: Optional[dict] = Field(default={})
    allergies: Optional[List[dict]] = Field(default=[])

    @validator('disease', each_item=True)
    def sanitize_disease(cls, v):
        # Remove special characters to prevent injection
        sanitized = re.sub(r'[^a-zA-Z0-9\s-]', '', str(v))
        return sanitized.strip()

    @validator('severity')
    def validate_severity(cls, v):
        if not v: return {}
        allowed_severities = {"Mild", "Moderate", "Severe"}
        for k, sev in v.items():
            if sev not in allowed_severities:
                v[k] = "Moderate" # Default sanitization
        return v


class HealthProfileCreate(HealthProfileBase):
    bmi: Optional[float] = None


class HealthStep1(BaseModel):
    age: int = Field(..., ge=1, le=120)
    gender: str
    weight_kg: float = Field(..., ge=10, le=500)
    height_cm: float = Field(..., ge=50, le=300)
    dietary_preference: str = Field(..., pattern='^(Veg|Vegan|Non-Veg)$')


class HealthStep2(BaseModel):
    disease: List[str]
    severity: dict
    health_values: dict
    allergies: List[dict]

    @validator('disease', each_item=True)
    def sanitize_disease(cls, v):
        sanitized = re.sub(r'[^a-zA-Z0-9\s-]', '', str(v))
        return sanitized.strip()

    @validator('severity')
    def validate_severity(cls, v):
        if not v: return {}
        allowed_severities = {"Mild", "Moderate", "Severe"}
        for k, sev in v.items():
            if sev not in allowed_severities:
                v[k] = "Moderate" # Default sanitization
        return v


class HealthReportResponse(BaseModel):
    age: int
    gender: str
    weight_kg: float
    height_cm: float
    bmi: float
    bmi_category: str
    disease: List[str]
    allergies: List[dict]
    risk_score: int
    risk_level: str
    recommendations: List[str]


class HealthProfileResponse(HealthProfileBase):
    id: int
    user_id: int
    name: Optional[str] = None
    bmi: float
    bmi_category: str
    diabetes_status: str
    bp_status: str
    cholesterol_status: str
    risk_score: int
    risk_level: str

    class Config:
        from_attributes = True


# Order schemas
class OrderCreate(BaseModel):
    items: List[int]
    total_price: float
    total_calories: float
    total_sugar: float
    total_sodium: float


class OrderResponse(OrderCreate):
    id: int
    user_id: int
    created_at: str

    class Config:
        from_attributes = True


# Daily Log schemas
class DailyLogCreate(BaseModel):
    water_intake_ml: Optional[int] = 0
    steps: Optional[int] = 0
    mood: Optional[str] = "Neutral"


class DailyLogResponse(DailyLogCreate):
    id: int
    user_id: int
    date: str

    class Config:
        from_attributes = True
