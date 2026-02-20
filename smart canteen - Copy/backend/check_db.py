import sqlite3
import os

db_path = "canteen.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("Users table columns:")
    for col in columns:
        print(col[1])
    
    cursor.execute("PRAGMA table_info(health_profiles)")
    columns = cursor.fetchall()
    print("\nHealth Profiles table columns:")
    for col in columns:
        print(col[1])
    conn.close()
else:
    print("Database not found")
