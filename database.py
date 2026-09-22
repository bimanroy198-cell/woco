import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)

db = client["woco_db"]

workers_collection = db["workers"]
contractors_collection = db["contractors"]
otp_collection = db["otps"]
jobs_collection = db["jobs"]
applications_collection = db["applications"]
messages_collection = db["messages"]

# Phase 2: Unified Admin Panel Collections
admin_users_collection = db["admin_users"]
app_updates_collection = db["app_updates"]
website_content_collection = db["website_content"]
admin_audit_logs_collection = db["admin_audit_logs"]

# Create required indexes for performance and uniqueness
# (Indexes should be created once manually or via a separate script, not on every Vercel cold start)