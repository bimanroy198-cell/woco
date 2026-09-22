import os
from dotenv import load_dotenv
from flask import Flask, send_from_directory
from flask_cors import CORS

# Load env variables before importing routes that might depend on them
load_dotenv()

from routes.auth_routes import auth_bp
from routes.worker_routers import worker_bp
from routes.contractor_routers import contractor_bp
from routes.public_routes import public_bp
from routes.job_routes import job_bp
from routes.application_routes import application_bp
from routes.chat_routes import chat_bp
from routes.update_routes import update_bp
from routes.admin_api import admin_api_bp
from routes.admin_ui_routes import admin_ui_bp

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_woco_key")
CORS(app)

app.register_blueprint(public_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(worker_bp)
app.register_blueprint(contractor_bp)
app.register_blueprint(job_bp)
app.register_blueprint(application_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(update_bp)
app.register_blueprint(admin_api_bp)
app.register_blueprint(admin_ui_bp)

# Route to serve uploaded images
@app.route('/uploads/<filename>')
def serve_upload(filename):
    return send_from_directory('uploads', filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False
    )
