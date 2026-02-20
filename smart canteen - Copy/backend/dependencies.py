from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models import User
from database import get_db
from jose import JWTError, jwt
import os

# JWT configuration - In production, use environment variables
# JWT configuration - Required in production
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    if os.environ.get("ENV") == "production":
        raise RuntimeError("JWT_SECRET_KEY must be set in production environment")
    SECRET_KEY = "dev-secret-key-only-for-local-testing"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

from datetime import datetime
from collections import defaultdict

# Simple In-Memory Rate Limiter Config
# Dictionary of {ip/user: [timestamp1, timestamp2, ...]}
rate_limit_store = defaultdict(list)
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SEC = 60

async def check_rate_limit(
    current_user: User = Depends(get_current_user)
):
    """
    Dependency to enforce rate limiting primarily on sensitive routes like Health records.
    Limits to RATE_LIMIT_REQUESTS per RATE_LIMIT_WINDOW_SEC per user ID.
    """
    user_key = f"user_{current_user.id}"
    now = datetime.now()
    
    # Filter valid timestamps within the last window
    valid_times = [t for t in rate_limit_store[user_key] if (now - t).total_seconds() <= RATE_LIMIT_WINDOW_SEC]
    
    if len(valid_times) >= RATE_LIMIT_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
        
    # Valid request, append time and update store
    valid_times.append(now)
    rate_limit_store[user_key] = valid_times
    
    return True


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user from JWT token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"DEBUG: JWT Payload: {payload}")
        email: str = payload.get("sub")
        if email is None:
            print("DEBUG: email (sub) is None in payload")
            raise credentials_exception
    except JWTError as e:
        print(f"DEBUG: JWT Decode Error: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        print(f"DEBUG: User not found for email: {email}")
        raise credentials_exception
    
    return user

