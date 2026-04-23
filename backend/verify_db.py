import sys
import os

# Add backend to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.database import SessionLocal
from app.services.user.user_service import UserService

def verify():
    print("Testing DB Integration...")
    db = SessionLocal()
    try:
        # Simulate an OTP login which triggers an upsert
        phone = "+919999999999"
        print(f"Attempting to upsert user for {phone}")
        user = UserService.upsert_user(db, phone)
        
        if user and user.id:
            print(f"SUCCESS! \u2705 User created in PostgreSQL successfully! User ID: {user.id}")
        else:
            print("FAILURE! \u274C User not created successfully.")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    verify()
