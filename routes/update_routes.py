from flask import Blueprint, jsonify, request
from database import db

update_bp = Blueprint("update_bp", __name__)

@update_bp.route("/check-update", methods=["GET"])
def check_update():
    try:
        current_version_code = request.args.get("version_code", type=int, default=0)
        
        # Find the latest android update (sort by version_code descending)
        latest_update = db["app_updates"].find_one(
            {"platform": "android", "status": "published"},
            sort=[("version_code", -1)]
        )
        
        if not latest_update:
            return jsonify({"updateAvailable": False}), 200
            
        latest_version = latest_update.get("version_code", 0)
        
        if latest_version > current_version_code:
            return jsonify({
                "updateAvailable": True,
                "latestVersionCode": latest_version,
                "latestVersionName": latest_update.get("version_name", ""),
                "apkUrl": latest_update.get("apk_url", latest_update.get("update_url", "")),
                "sha256": latest_update.get("sha256", ""),
                "forceUpdate": latest_update.get("force_update", False),
                "changelog": latest_update.get("changelog", "")
            }), 200
        else:
            return jsonify({"updateAvailable": False}), 200
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500