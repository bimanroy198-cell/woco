import os
import random
import time
import requests
from flask import Blueprint, request, jsonify
from database import otp_collection

auth_bp = Blueprint("auth_bp", __name__)

FAST2SMS_API_KEY = os.environ.get("FAST2SMS_API_KEY")
FAST2SMS_OTP_ID = os.environ.get("FAST2SMS_OTP_ID")

@auth_bp.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json()
    if not data or "mobile" not in data:
        return jsonify({"error": "Mobile number is required"}), 400
    
    mobile = data["mobile"]
    is_test_mode = data.get("isTestMode", False)

    # Format mobile number: Fast2SMS needs plain 10-digit number
    if mobile.startswith("+91"):
        sms_mobile = mobile[3:]       # +919876543210 → 9876543210
    elif mobile.startswith("91") and len(mobile) == 12:
        sms_mobile = mobile[2:]       # 919876543210  → 9876543210
    elif len(mobile) == 10:
        sms_mobile = mobile           # already 10-digit
    else:
        sms_mobile = mobile

    # Rate limiting: Check if an OTP was requested recently (within 60 seconds)
    existing_record = otp_collection.find_one({"mobile": mobile})
    current_time = int(time.time())
    if existing_record:
        last_requested = existing_record.get("requested_at", 0)
        if current_time - last_requested < 60:
            return jsonify({"error": "Please wait 60 seconds before requesting another OTP"}), 429
    
    # Generate 6-digit OTP (Fixed for Test Mode)
    otp = "123456" if is_test_mode else f"{random.randint(0, 999999):06d}"
    
    # Save OTP to database with expiration timestamp (e.g., 5 minutes)
    expiration = current_time + 300
    otp_collection.update_one(
        {"mobile": mobile},
        {"$set": {"otp": otp, "expiration": expiration, "requested_at": current_time}},
        upsert=True
    )
    
    # If in test mode, return success immediately without calling API
    if is_test_mode:
        return jsonify({"success": True, "message": f"Test Mode: OTP is {otp}"}), 200
        
    # Call Fast2SMS Bulk V2 API (Quick Route)
    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": FAST2SMS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "route": "q",
        "message": f"{otp} is your verification code for WOCO App.",
        "language": "english",
        "flash": 0,
        "numbers": sms_mobile
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("return") == True:
            return jsonify({"success": True, "message": "OTP sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send OTP via SMS provider", "details": response_data}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from database import workers_collection, contractors_collection
from datetime import datetime

@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()
    if not data or "mobile" not in data or "enteredOtp" not in data:
        return jsonify({"error": "Mobile and enteredOtp are required"}), 400
        
    mobile = data["mobile"]
    entered_otp = data["enteredOtp"]
    
    record = otp_collection.find_one({"mobile": mobile})
    
    if not record:
        return jsonify({"success": False, "message": "OTP not found for this mobile"}), 404
        
    if int(time.time()) > record.get("expiration", 0):
        return jsonify({"success": False, "message": "OTP has expired"}), 400
        
    if record.get("otp") == entered_otp:
        # OTP matched, clean it up
        otp_collection.delete_one({"mobile": mobile})
        
        # Check User Profile in both collections
        user = workers_collection.find_one({"phone_number": mobile}, {"_id": 0})
        role = "worker"
        
        if not user:
            user = contractors_collection.find_one({"phone_number": mobile}, {"_id": 0})
            role = "contractor" if user else None
            
        if user:
            # Check Blocked or Deleted
            is_blocked = user.get("is_blocked", False)
            is_deleted = user.get("is_deleted", False)
            
            if is_blocked:
                # Return HTTP 200 so Retrofit onResponse handles it properly
                return jsonify({"success": True, "exists": True, "blocked": True, "deleted": is_deleted, "message": "Your account has been blocked by Admin."}), 200
            
            if is_deleted:
                # Return HTTP 200 so Retrofit onResponse handles it properly
                return jsonify({"success": True, "exists": True, "blocked": False, "deleted": True, "message": "Your account is deleted."}), 200

            # Update last_login
            now_iso = datetime.utcnow().isoformat()
            if role == "worker":
                workers_collection.update_one({"phone_number": mobile}, {"$set": {"last_login": now_iso}})
            else:
                contractors_collection.update_one({"phone_number": mobile}, {"$set": {"last_login": now_iso}})
            
            return jsonify({
                "success": True,
                "exists": True,
                "blocked": False,
                "deleted": False,
                "role": role,
                "profile_completed": user.get("profile_completed", True),
                "user": {
                    "name": user.get("name", ""),
                    "photo_url": user.get("profile_photo_url", ""),
                    "location": user.get("location", ""),
                    "skills": user.get("categories", []),
                    "about": user.get("about", ""),
                    "experience": user.get("experience", ""),
                    "age": user.get("age", "")
                }
            }), 200
        else:
            # User does not exist, prompt registration
            return jsonify({
                "success": True, 
                "exists": False,
                "blocked": False,
                "deleted": False
            }), 200
    else:
        return jsonify({"success": False, "message": "Invalid OTP"}), 400

@auth_bp.route("/delete-account", methods=["POST"])
def delete_account():
    data = request.get_json()
    if not data or "mobile" not in data or "role" not in data:
        return jsonify({"success": False, "message": "Mobile and role required"}), 400
        
    mobile = data["mobile"]
    role = data["role"]
    
    update_data = {
        "is_deleted": True,
        "deleted_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    if role == "worker":
        result = workers_collection.update_one({"phone_number": mobile}, {"$set": update_data})
    else:
        result = contractors_collection.update_one({"phone_number": mobile}, {"$set": update_data})
        
    if result.matched_count == 0:
        return jsonify({"success": False, "message": "User not found"}), 404
        
    return jsonify({"success": True, "message": "Account deleted successfully"})

@auth_bp.route("/google-login", methods=["POST"])
def google_login():
    data = request.get_json()
    if not data or "email" not in data:
        return jsonify({"error": "Email is required"}), 400
    
    email = data["email"]
    name = data.get("name", "")
    photo_url = data.get("photo_url", "")
    
    # Check if user exists in workers or contractors collection (by email)
    user = workers_collection.find_one({"email": email}, {"_id": 0})
    role = "worker"
    
    if not user:
        user = contractors_collection.find_one({"email": email}, {"_id": 0})
        role = "contractor" if user else None
    
    if user:
        # Check Blocked or Deleted
        is_blocked = user.get("is_blocked", False)
        is_deleted = user.get("is_deleted", False)
        
        if is_blocked:
            return jsonify({
                "success": True, "exists": True,
                "blocked": True, "deleted": is_deleted,
                "message": "Your account has been blocked by Admin."
            }), 200
        
        if is_deleted:
            return jsonify({
                "success": True, "exists": True,
                "blocked": False, "deleted": True,
                "message": "Your account is deleted."
            }), 200
        
        # Update last_login
        now_iso = datetime.utcnow().isoformat()
        if role == "worker":
            workers_collection.update_one({"email": email}, {"$set": {"last_login": now_iso}})
        else:
            contractors_collection.update_one({"email": email}, {"$set": {"last_login": now_iso}})
        
        return jsonify({
            "success": True,
            "exists": True,
            "blocked": False,
            "deleted": False,
            "role": role,
            "profile_completed": user.get("profile_completed", True),
            "user": {
                "phone_number": user.get("phone_number", ""),
                "name": user.get("name", ""),
                "photo_url": user.get("profile_photo_url", ""),
                "location": user.get("location", ""),
                "skills": user.get("categories", []),
                "about": user.get("about", ""),
                "experience": user.get("experience", ""),
                "age": user.get("age", "")
            }
        }), 200
    else:
        # User does not exist — prompt registration
        return jsonify({
            "success": True,
            "exists": False,
            "blocked": False,
            "deleted": False
        }), 200
