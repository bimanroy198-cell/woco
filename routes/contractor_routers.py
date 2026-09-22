import os
import cloudinary
import cloudinary.uploader
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from database import contractors_collection

# Configure cloudinary if env vars are present
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET")
)

contractor_bp = Blueprint("contractor_bp", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure folder exists

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@contractor_bp.route("/register-contractor", methods=["POST"])
def register_contractor():
    try:
        phone_number = request.form.get("phone_number")
        
        # Validation: Phone number is mandatory
        if not phone_number:
            return jsonify({
                "success": False, 
                "message": "Phone number is required"
            }), 400

        role = request.form.get("role")
        name = request.form.get("name")
        categories = request.form.getlist("categories")
        
        photo = request.files.get("photo")
        photo_path = ""

        if photo and photo.filename:
            if allowed_file(photo.filename):
                import time
                filename = secure_filename(f"{phone_number}_{int(time.time())}_{photo.filename}")
                
                # Check if Cloudinary is configured
                if os.environ.get("CLOUDINARY_CLOUD_NAME"):
                    try:
                        upload_result = cloudinary.uploader.upload(photo, folder="woco/profiles")
                        photo_path = upload_result.get("secure_url")
                    except Exception as e:
                        return jsonify({"success": False, "message": f"Cloudinary upload failed: {str(e)}"}), 500
                else:
                    # Fallback to local storage
                    filepath = os.path.join(UPLOAD_FOLDER, filename)
                    photo.save(filepath)
                    photo_path = f"/uploads/{filename}"
            else:
                return jsonify({
                    "success": False, 
                    "message": "Invalid image format. Only PNG, JPG, WEBP allowed."
                }), 400

        from datetime import datetime
        now_iso = datetime.utcnow().isoformat()

        contractor_data = {
            "phone_number": phone_number,
            "email": request.form.get("email", ""),
            "role": role,
            "name": name,
            "categories": categories,
            "location": request.form.get("location", ""),
            "about": request.form.get("about", ""),
            "experience": request.form.get("experience", ""),
            "age": request.form.get("age", ""),
            "profile_completed": True,
            "is_blocked": False,
            "blocked_at": None,
            "is_deleted": False,
            "deleted_at": None,
            "updated_at": now_iso
        }
        
        if photo_path:
            contractor_data["profile_photo_url"] = photo_path

        existing_user = contractors_collection.find_one({"phone_number": phone_number})

        if existing_user:
            contractors_collection.update_one(
                {"phone_number": phone_number},
                {"$set": contractor_data}
            )
        else:
            contractor_data["created_at"] = now_iso
            contractor_data["last_login"] = now_iso
            contractors_collection.insert_one(contractor_data)

        return jsonify({
            "success": True,
            "message": "Profile Saved"
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@contractor_bp.route("/get-profile", methods=["GET"])
def get_profile():
    phone_number = request.args.get("phone_number")
    if not phone_number:
        return jsonify({"success": False, "message": "Phone number required"}), 400
        
    user = contractors_collection.find_one({"phone_number": phone_number}, {"_id": 0})
    if user:
        return jsonify({"success": True, "profile": user})
    return jsonify({"success": False, "message": "User not found"}), 404

@contractor_bp.route("/contractor/update-profile", methods=["POST"])
def update_profile():
    try:
        phone_number = request.form.get("phone_number")
        if not phone_number:
            return jsonify({"success": False, "message": "Phone number is required"}), 400

        name = request.form.get("name")
        location = request.form.get("location")
        about = request.form.get("about")
        experience = request.form.get("experience")
        
        photo = request.files.get("photo")
        photo_path = None

        if photo and photo.filename:
            if not allowed_file(photo.filename):
                return jsonify({"success": False, "message": "Invalid format. Only JPG, JPEG, PNG allowed."}), 400
            
            # Check 5MB limit
            photo.seek(0, os.SEEK_END)
            size = photo.tell()
            photo.seek(0)
            if size > 5 * 1024 * 1024:
                return jsonify({"success": False, "message": "File too large. Max 5MB allowed."}), 400

            import time
            filename = secure_filename(f"{phone_number}_{int(time.time())}_{photo.filename}")
            
            # Check if Cloudinary is configured
            if os.environ.get("CLOUDINARY_CLOUD_NAME"):
                try:
                    upload_result = cloudinary.uploader.upload(photo, folder="woco/profiles")
                    photo_path = upload_result.get("secure_url")
                except Exception as e:
                    return jsonify({"success": False, "message": f"Cloudinary upload failed: {str(e)}"}), 500
            else:
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                photo.save(filepath)
                photo_path = f"/uploads/{filename}"

        update_data = {}
        if name is not None: update_data["name"] = name
        if location is not None: update_data["location"] = location
        if about is not None: update_data["about"] = about
        if experience is not None: update_data["experience"] = experience
        age = request.form.get("age")
        if age is not None: update_data["age"] = age
        if photo_path: update_data["profile_photo_url"] = photo_path

        categories_str = request.form.get("categories")
        if categories_str is not None:
            cats = [c.strip() for c in categories_str.split(",") if c.strip()]
            update_data["categories"] = cats

        if not update_data:
            return jsonify({"success": False, "message": "No data provided to update"}), 400

        from datetime import datetime
        update_data["updated_at"] = datetime.utcnow().isoformat()

        result = contractors_collection.update_one(
            {"phone_number": phone_number},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Contractor not found"}), 404

        return jsonify({
            "success": True,
            "message": "Profile updated successfully",
            "photo_url": photo_path
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@contractor_bp.route("/contractor/get-contractors", methods=["GET"])
def get_all_contractors():
    try:
        contractors = list(contractors_collection.find({"is_deleted": {"$ne": True}, "is_blocked": {"$ne": True}}, {"_id": 0}))
        return jsonify({
            "success": True,
            "data": contractors
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
