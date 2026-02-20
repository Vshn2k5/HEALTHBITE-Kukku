from database import SessionLocal
from models import User
import json

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"ID: {u.id}, Name: {u.name}, Email: {u.email}")
db.close()
