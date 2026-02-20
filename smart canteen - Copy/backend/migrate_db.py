import sqlite3
import os

db_path = "canteen.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Migrating users table...")
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN profile_completed INTEGER DEFAULT 0")
        print("Added profile_completed to users")
    except Exception as e:
        print(f"Skipped profile_completed: {e}")
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN onboarding_step INTEGER DEFAULT 0")
        print("Added onboarding_step to users")
    except Exception as e:
        print(f"Skipped onboarding_step: {e}")

    print("\nMigrating health_profiles table...")
    try:
        cursor.execute("ALTER TABLE health_profiles ADD COLUMN bmi_category TEXT DEFAULT 'Normal'")
        print("Added bmi_category to health_profiles")
    except Exception as e:
        print(f"Skipped bmi_category: {e}")
        
    try:
        cursor.execute("ALTER TABLE health_profiles ADD COLUMN risk_score INTEGER DEFAULT 0")
        print("Added risk_score to health_profiles")
    except Exception as e:
        print(f"Skipped risk_score: {e}")
        
    try:
        cursor.execute("ALTER TABLE health_profiles ADD COLUMN risk_level TEXT DEFAULT 'Low'")
        print("Added risk_level to health_profiles")
    except Exception as e:
        print(f"Skipped risk_level: {e}")

    conn.commit()
    conn.close()
    print("\nMigration complete.")
else:
    print("Database not found")
