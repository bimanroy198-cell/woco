import os
import time
import uuid
import base64
import hashlib
import bcrypt
from datetime import datetime, timezone
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify, session
from database import admin_audit_logs_collection, admin_users_collection, app_updates_collection, website_content_collection

admin_api_bp = Blueprint("admin_api", __name__)

failed_login_attempts = {}

def log_admin_action(admin_email, action, target, success, meta=None):
    admin_audit_logs_collection.insert_one({
        "admin_email": admin_email,
        "action": action,
        "target": target,
        "success": success,
        "meta": meta or {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

def _record_failed_attempt(ip, now):
    if ip not in failed_login_attempts:
        failed_login_attempts[ip] = {"attempts": 1, "locked_until": 0}
    failed_login_attempts[ip]["attempts"] += 1
    if failed_login_attempts[ip]["attempts"] >= 5:
        failed_login_attempts[ip]["locked_until"] = now + 900

@admin_api_bp.route("/api/admin/login", methods=["POST"])
def api_admin_login():
    client_ip = request.remote_addr
    now = datetime.now(timezone.utc).timestamp()
    
    if client_ip in failed_login_attempts:
        if now < failed_login_attempts[client_ip]["locked_until"]:
            return jsonify({"success": False, "message": "Too many failed attempts. Try again in 15 minutes."}), 429
        elif now > failed_login_attempts[client_ip]["locked_until"] and failed_login_attempts[client_ip]["attempts"] >= 5:
            failed_login_attempts[client_ip] = {"attempts": 0, "locked_until": 0}

    data = request.get_json() or {}
    email = data.get("email", "")
    password = data.get("password", "")
    
    admin_user = admin_users_collection.find_one({"email": email})
    
    if admin_user:
        hashed_db = admin_user.get("password_hash", "")
        if isinstance(hashed_db, str):
            hashed_db = hashed_db.encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), hashed_db):
            session["api_admin_email"] = email
            if client_ip in failed_login_attempts:
                failed_login_attempts.pop(client_ip)
            log_admin_action(email, "LOGIN", "system", True)
            return jsonify({"success": True, "message": "Logged in successfully"})
        
    _record_failed_attempt(client_ip, now)
    log_admin_action(email, "LOGIN", "system", False, {"ip": client_ip})
    return jsonify({"success": False, "message": "Invalid email or password"}), 401
    
@admin_api_bp.route("/api/admin/logout", methods=["POST"])
def api_admin_logout():
    email = session.get("api_admin_email")
    if email:
        log_admin_action(email, "LOGOUT", "system", True)
        session.pop("api_admin_email", None)
    return jsonify({"success": True})

@admin_api_bp.route("/api/admin/me", methods=["GET"])
def api_admin_me():
    email = session.get("api_admin_email")
    if not email:
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    return jsonify({"success": True, "email": email})

@admin_api_bp.route("/api/admin/publish", methods=["POST"])
def publish_release():
    try:
        if not session.get("api_admin_email"):
            return jsonify({"success": False, "message": "Unauthorized"}), 401
            
        version_code = int(request.form.get("version_code", 0))
        version_name = request.form.get("version_name", "")
        changelog = request.form.get("changelog", "")
        force_update = request.form.get("force_update") == "true"
        
        apk_file = request.files.get("apk_file")
        if not apk_file:
            return jsonify({"success": False, "message": "APK missing"}), 400
            
        filename = secure_filename(apk_file.filename)
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        save_path = os.path.join(upload_dir, filename)
        apk_file.save(save_path)
        
        sha256_hash = hashlib.sha256()
        with open(save_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        sha256 = sha256_hash.hexdigest()
        
        app_updates_collection.insert_one({
            "platform": "android",
            "version_code": version_code,
            "version_name": version_name,
            "changelog": changelog,
            "force_update": force_update,
            "apk_url": f"/uploads/{filename}",
            "sha256": sha256,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        log_admin_action(session.get("api_admin_email"), "PUBLISH_APK", filename, True, {"version": version_name})
        return jsonify({"success": True, "message": "Release published!"})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

@admin_api_bp.route("/api/admin/cms", methods=["POST"])
def update_cms():
    if not session.get("api_admin_email"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    hero_title = request.form.get("hero_title")
    hero_subtitle = request.form.get("hero_subtitle")
    
    if not hero_title or not hero_subtitle:
        return jsonify({"success": False, "message": "Title and subtitle are required"}), 400
        
    current_content = website_content_collection.find_one({"_id": "main_content"}) or {}
    
    hero_image = request.files.get("hero_image")
    new_hero_image_url = None
    
    if hero_image and hero_image.filename:
        image_bytes = hero_image.read()
        b64_string = base64.b64encode(image_bytes).decode('utf-8')
        mime_type = hero_image.content_type or "image/jpeg"
        new_hero_image_url = f"data:{mime_type};base64,{b64_string}"
    
    update_data = {
        "hero_title": hero_title,
        "hero_subtitle": hero_subtitle,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": session.get("api_admin_email")
    }
    if new_hero_image_url:
        update_data["hero_image_url"] = new_hero_image_url
        
    website_content_collection.update_one(
        {"_id": "main_content"},
        {"$set": update_data},
        upsert=True
    )
    
    log_admin_action(session.get("api_admin_email"), "UPDATE_CMS", "main_content", True)
    return jsonify({"success": True, "message": "Website content updated successfully!"})

@admin_api_bp.route("/api/admin/users", methods=["GET"])
def get_all_users():
    if not session.get("api_admin_email"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    from database import workers_collection, contractors_collection
    
    workers = list(workers_collection.find({}, {"_id": 0}))
    for w in workers:
        w["type"] = "Worker"
        
    contractors = list(contractors_collection.find({}, {"_id": 0}))
    for c in contractors:
        c["type"] = "Contractor"
        
    all_users = workers + contractors
    all_users.sort(key=lambda x: x.get("updated_at", x.get("created_at", "")), reverse=True)
    
    return jsonify({"success": True, "users": all_users})

@admin_api_bp.route("/api/admin/users/block", methods=["POST"])
def admin_block_user():
    if not session.get("api_admin_email"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.json or {}
    phone = data.get("phone")
    user_type = data.get("type")
    block_status = data.get("block_status", False)
    
    from database import workers_collection, contractors_collection
    collection = workers_collection if user_type == "Worker" else contractors_collection
    
    result = collection.update_one({"phone_number": phone}, {"$set": {"is_blocked": block_status}})
    
    if result.modified_count > 0 or result.matched_count > 0:
        log_admin_action(session.get("api_admin_email"), "BLOCK_USER", "system", True, {"phone": phone, "blocked": block_status})
        return jsonify({"success": True, "message": f"User {'blocked' if block_status else 'unblocked'} successfully."})
    else:
        return jsonify({"success": False, "message": "User not found."}), 404

@admin_api_bp.route("/api/admin/users/delete", methods=["DELETE"])
def admin_delete_user():
    if not session.get("api_admin_email"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
    
    data = request.json or {}
    phone = data.get("phone")
    user_type = data.get("type")
    
    from database import workers_collection, contractors_collection
    collection = workers_collection if user_type == "Worker" else contractors_collection
    
    result = collection.delete_one({"phone_number": phone})
    
    if result.deleted_count > 0:
        log_admin_action(session.get("api_admin_email"), "DELETE_USER", "system", True, {"phone": phone})
        return jsonify({"success": True, "message": "User PERMANENTLY deleted."})
    else:
        return jsonify({"success": False, "message": "User not found."}), 404
