import os
import bcrypt
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client["woco_db"]
admin_users = db["admin_users"]

def create_superadmin():
    email = input("Enter admin email: ").strip()
    password = input("Enter admin password: ").strip()
    
    if not email or not password:
        print("Email and password are required.")
        return
        
    existing = admin_users.find_one({"email": email})
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    if existing:
        # Update existing admin password
        admin_users.update_one(
            {"email": email},
            {"$set": {"password_hash": hashed.decode('utf-8')}}
        )
        print(f"Success! Password for existing admin '{email}' has been updated.")
    else:
        # Create new admin
        admin_users.insert_one({
            "email": email,
            "password_hash": hashed.decode('utf-8'),
            "role": "superadmin",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        print(f"Success! Superadmin '{email}' created successfully.")
        
    print("You can now login at /woco-admin")

if __name__ == "__main__":
    create_superadmin()