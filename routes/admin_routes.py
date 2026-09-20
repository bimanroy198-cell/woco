from flask import Blueprint, render_template_string, request, jsonify, session, redirect, url_for
from database import workers_collection, contractors_collection
from datetime import datetime
import os

admin_bp = Blueprint("admin_bp", __name__)

ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "12biman345") # Default for testing

HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Admin Login</title></head>
<body style="font-family: Arial; background: #f4f4f4; display: flex; justify-content: center; align-items: center; height: 100vh;">
    <div style="background: white; padding: 40px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center;">
        <h2>Admin Login</h2>
        {% if error %}<p style="color: red;">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Admin Password" required style="padding: 10px; width: 200px; margin-bottom: 20px;"><br>
            <button type="submit" style="padding: 10px 20px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer;">Login</button>
        </form>
    </div>
</body>
</html>
"""

HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head>
    <title>WOCO Admin Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f4f4f4; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        h1 { color: #333; }
        .table-container { background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 30px; overflow-x: auto;}
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #007BFF; color: white; }
        img { width: 50px; height: 50px; border-radius: 50%; object-fit: cover; }
        .badge { padding: 4px 8px; border-radius: 12px; color: white; font-size: 12px; font-weight: bold; }
        .active { background-color: #28a745; }
        .blocked { background-color: #dc3545; }
        .deleted { background-color: #6c757d; }
        button { padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; margin-right: 5px; color: white;}
        .btn-block { background-color: #ffc107; color: black; }
        .btn-unblock { background-color: #28a745; }
        .btn-delete { background-color: #fd7e14; }
        .btn-hard-delete { background-color: #8b0000; color: white; }
        .btn-logout { background-color: #333; padding: 10px 20px;}
    </style>
</head>
<body>
    <div class="header">
        <h1>WOCO Admin Dashboard</h1>
        <form action="/admin/logout" method="GET">
            <button type="submit" class="btn-logout">Logout</button>
        </form>
    </div>

    <!-- Workers Table -->
    <div class="table-container">
        <h2>Workers</h2>
        <table>
            <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>Phone</th>
                <th>Location</th>
                <th>About</th>
                <th>Experience</th>
                <th>Skills</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
            {% for worker in workers %}
            <tr>
                <td>{% if worker.profile_photo_url %}<img src="{{ worker.profile_photo_url }}">{% else %}No Photo{% endif %}</td>
                <td>{{ worker.name }}</td>
                <td>{{ worker.phone_number }}</td>
                <td>{{ worker.location or 'N/A' }}</td>
                <td>{{ worker.about or 'N/A' }}</td>
                <td>{{ worker.experience or 'N/A' }}</td>
                <td>
                    {% if worker.categories %}
                        {% for skill in worker.categories %}
                            <span class="badge" style="background-color: #6f42c1; margin: 2px; display: inline-block;">{{ skill }}</span>
                        {% endfor %}
                    {% else %}
                        N/A
                    {% endif %}
                </td>
                <td>
                    {% if worker.is_deleted %}
                        <span class="badge deleted">Deleted</span>
                    {% elif worker.is_blocked %}
                        <span class="badge blocked">Blocked</span>
                    {% else %}
                        <span class="badge active">Active</span>
                    {% endif %}
                </td>
                <td>
                    <button class="btn-block" onclick="updateStatus('{{ worker.phone_number }}', 'worker', 'block')">Block</button>
                    <button class="btn-unblock" onclick="updateStatus('{{ worker.phone_number }}', 'worker', 'unblock')">Unblock</button>
                    <button class="btn-delete" onclick="updateStatus('{{ worker.phone_number }}', 'worker', 'delete')">Soft Delete</button>
                    <button class="btn-hard-delete" onclick="hardDelete('{{ worker.phone_number }}', 'worker')">Hard Delete</button>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <!-- Contractors Table -->
    <div class="table-container">
        <h2>Contractors</h2>
        <table>
            <tr>
                <th>Photo</th>
                <th>Name</th>
                <th>Phone</th>
                <th>Location</th>
                <th>About</th>
                <th>Experience</th>
                <th>Status</th>
                <th>Actions</th>
            </tr>
            {% for contractor in contractors %}
            <tr>
                <td>{% if contractor.profile_photo_url %}<img src="{{ contractor.profile_photo_url }}">{% else %}No Photo{% endif %}</td>
                <td>{{ contractor.name }}</td>
                <td>{{ contractor.phone_number }}</td>
                <td>{{ contractor.location or 'N/A' }}</td>
                <td>{{ contractor.about or 'N/A' }}</td>
                <td>{{ contractor.experience or 'N/A' }}</td>
                <td>
                    {% if contractor.is_deleted %}
                        <span class="badge deleted">Deleted</span>
                    {% elif contractor.is_blocked %}
                        <span class="badge blocked">Blocked</span>
                    {% else %}
                        <span class="badge active">Active</span>
                    {% endif %}
                </td>
                <td>
                    <button class="btn-block" onclick="updateStatus('{{ contractor.phone_number }}', 'contractor', 'block')">Block</button>
                    <button class="btn-unblock" onclick="updateStatus('{{ contractor.phone_number }}', 'contractor', 'unblock')">Unblock</button>
                    <button class="btn-delete" onclick="updateStatus('{{ contractor.phone_number }}', 'contractor', 'delete')">Soft Delete</button>
                    <button class="btn-hard-delete" onclick="hardDelete('{{ contractor.phone_number }}', 'contractor')">Hard Delete</button>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <script>
        function updateStatus(phone, role, action) {
            if(!confirm("Are you sure you want to " + action + " this user?")) return;
            
            fetch('/admin/' + action, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, role: role })
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    location.reload();
                } else {
                    alert(data.message);
                }
            });
        }

        function hardDelete(phone, role) {
            let confirmation = prompt("This will PERMANENTLY delete the user. Type DELETE to confirm:");
            if(confirmation !== "DELETE") {
                alert("Action cancelled.");
                return;
            }
            fetch('/admin/hard-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: phone, role: role })
            }).then(res => res.json()).then(data => {
                if(data.success) {
                    location.reload();
                } else {
                    alert(data.message);
                }
            });
        }
    </script>
</body>
</html>
"""

@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_bp.admin_dashboard"))
        return render_template_string(HTML_LOGIN, error="Invalid password")
    return render_template_string(HTML_LOGIN)

@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_bp.admin_login"))

@admin_bp.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_bp.admin_login"))
        
    workers = list(workers_collection.find({}, {"_id": 0}))
    contractors = list(contractors_collection.find({}, {"_id": 0}))
    return render_template_string(HTML_DASHBOARD, workers=workers, contractors=contractors)

@admin_bp.route("/admin/<action>", methods=["POST"])
def admin_action(action):
    if not session.get("admin_logged_in"):
        return jsonify({"success": False, "message": "Unauthorized"}), 401
        
    data = request.get_json()
    phone = data.get("phone")
    role = data.get("role")
    
    if not phone or not role:
        return jsonify({"success": False, "message": "Phone and role required"}), 400
        
    collection = workers_collection if role == "worker" else contractors_collection
    
    if action == "hard-delete":
        collection.delete_one({"phone_number": phone})
        return jsonify({"success": True})
        
    now_iso = datetime.utcnow().isoformat()
    
    update_data = {}
    if action == "block":
        update_data = {"is_blocked": True, "blocked_at": now_iso}
    elif action == "unblock":
        update_data = {"is_blocked": False, "blocked_at": None}
    elif action == "delete":
        update_data = {"is_deleted": True, "deleted_at": now_iso}
    else:
        return jsonify({"success": False, "message": "Invalid action"}), 400
        
    collection.update_one({"phone_number": phone}, {"$set": update_data})
    return jsonify({"success": True})
