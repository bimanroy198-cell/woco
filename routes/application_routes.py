from flask import Blueprint, request, jsonify
from datetime import datetime
from database import applications_collection, jobs_collection, workers_collection

application_bp = Blueprint("application_bp", __name__)

@application_bp.route("/applications/apply", methods=["POST"])
def apply_to_job():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Invalid JSON"}), 400

        job_id = data.get("job_id")
        worker_phone = data.get("worker_phone")

        if not job_id or not worker_phone:
            return jsonify({"success": False, "message": "job_id and worker_phone required"}), 400

        # Check if job exists
        job = jobs_collection.find_one({"job_id": job_id})
        if not job:
            return jsonify({"success": False, "message": "Job not found"}), 404

        if job.get("status") != "active":
            return jsonify({"success": False, "message": "This job is no longer active"}), 400

        contractor_phone = job.get("contractor_phone")

        # Duplicate check
        existing_app = applications_collection.find_one({
            "job_id": job_id,
            "worker_phone": worker_phone
        })
        if existing_app:
            return jsonify({"success": False, "message": "Already applied"}), 400

        now_iso = datetime.utcnow().isoformat()

        application_data = {
            "job_id": job_id,
            "worker_phone": worker_phone,
            "contractor_phone": contractor_phone,
            "applied_at": now_iso,
            "status": "pending" # pending, shortlisted, rejected, hired
        }

        applications_collection.insert_one(application_data)

        return jsonify({
            "success": True,
            "message": "Application submitted successfully"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@application_bp.route("/applications/applicants", methods=["GET"])
def get_applicants():
    try:
        job_id = request.args.get("job_id")
        if not job_id:
            return jsonify({"success": False, "message": "job_id required"}), 400

        # Find all applications for this job
        apps = list(applications_collection.find({"job_id": job_id}, {"_id": 0}))
        
        # Hydrate with worker profile details
        for app in apps:
            worker = workers_collection.find_one({"phone_number": app["worker_phone"]}, {"_id": 0})
            if worker:
                app["worker_details"] = worker

        return jsonify({
            "success": True,
            "applications": apps
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@application_bp.route("/applications/update-status", methods=["POST"])
def update_status():
    try:
        data = request.get_json()
        job_id = data.get("job_id")
        worker_phone = data.get("worker_phone")
        new_status = data.get("status")

        if not job_id or not worker_phone or not new_status:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        valid_statuses = ["pending", "shortlisted", "rejected", "hired"]
        if new_status not in valid_statuses:
            return jsonify({"success": False, "message": "Invalid status"}), 400

        result = applications_collection.update_one(
            {"job_id": job_id, "worker_phone": worker_phone},
            {"$set": {"status": new_status}}
        )

        if result.matched_count == 0:
            return jsonify({"success": False, "message": "Application not found"}), 404

        return jsonify({"success": True, "message": f"Status updated to {new_status}"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
