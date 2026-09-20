from flask import Blueprint, render_template, redirect, url_for, flash
from database import website_content_collection, app_updates_collection

public_bp = Blueprint('public', __name__)

@public_bp.route("/")
def index():
    # Fetch website CMS data
    cms_data = website_content_collection.find_one({"_id": "main_content"}) or {}
    
    # Fetch the latest published app version to display dynamically
    latest_release = app_updates_collection.find_one(
        {"platform": "android", "status": "published"}, 
        sort=[("version_code", -1)]
    )
    latest_version = latest_release.get("version_name", "1.0") if latest_release else "1.0"
    
    return render_template("index.html", cms=cms_data, latest_version=latest_version)

@public_bp.route("/download-latest")
def download_latest():
    # Find the latest published android release
    latest_release = app_updates_collection.find_one(
        {"platform": "android", "status": "published"}, 
        sort=[("version_code", -1)]
    )
    
    # Check for apk_url or update_url (legacy support for the one release we did)
    url = latest_release.get("apk_url") or latest_release.get("update_url") if latest_release else None
    
    if url:
        return redirect(url)
    else:
        # If no APK is uploaded yet, redirect to home with a message
        return "App is not available for download yet. Check back soon!", 404
