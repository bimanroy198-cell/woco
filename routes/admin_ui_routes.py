from flask import Blueprint, render_template, session, redirect, url_for
from database import app_updates_collection, website_content_collection

admin_ui_bp = Blueprint("admin_ui_bp", __name__)

@admin_ui_bp.route("/woco-admin")
def woco_admin_login_page():
    # If already logged in via API session, redirect to dashboard
    if session.get("api_admin_email"):
        return redirect(url_for("admin_ui_bp.woco_admin_dashboard_page"))
    return render_template("woco_admin_login.html")

@admin_ui_bp.route("/woco-admin/dashboard")
def woco_admin_dashboard_page():
    if not session.get("api_admin_email"):
        return redirect(url_for("admin_ui_bp.woco_admin_login_page"))
        
    # Fetch data to display on dashboard
    releases = list(app_updates_collection.find({}, sort=[("version_code", -1)]))
    website_data = website_content_collection.find_one({"site_key": "main"}) or {}
    
    return render_template(
        "woco_admin_dashboard.html", 
        admin_email=session.get("api_admin_email"),
        releases=releases,
        website_data=website_data
    )