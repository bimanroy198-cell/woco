from flask import Blueprint, request, jsonify
import uuid
from datetime import datetime
from database import jobs_collection

job_bp = Blueprint("job_bp", __name__)

@job_bp.route("/jobs/create", methods=["POST"])
def create_job():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON"}), 400

        contractor_phone = data.get("contractor_phone")
        title = data.get("title")
        description = data.get("description")
        budget = data.get("budget")
        location = data.get("location")
        categories = data.get("categories", [])

        if not contractor_phone or not title or not description or not location:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        job_id = str(uuid.uuid4())
        now_iso = datetime.utcnow().isoformat()

        job_data = {
            "job_id": job_id,
            "contractor_phone": contractor_phone,
            "title": title,
            "description": description,
            "budget": budget,
            "location": location,
            "categories": categories,
            "status": "active",
            "created_at": now_iso,
            "updated_at": now_iso
        }

        jobs_collection.insert_one(job_data)

        # Remove _id for JSON serialization
        job_data.pop('_id', None)

        return jsonify({
            "success": True,
            "message": "Job created successfully",
            "job": job_data
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@job_bp.route("/jobs/feed", methods=["GET"])
def get_job_feed():
    try:
        # Fetch all active jobs
        jobs = list(jobs_collection.find({"status": "active"}, {"_id": 0}).sort("created_at", -1))
        return jsonify({
            "success": True,
            "jobs": jobs
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@job_bp.route("/jobs/my-jobs", methods=["GET"])
def get_my_jobs():
    try:
        contractor_phone = request.args.get("phone_number")
        if not contractor_phone:
            return jsonify({"success": False, "message": "phone_number required"}), 400

        jobs = list(jobs_collection.find({"contractor_phone": contractor_phone}, {"_id": 0}).sort("created_at", -1))
        return jsonify({
            "success": True,
            "jobs": jobs
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
