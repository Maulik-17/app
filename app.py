import os
import tempfile
import requests
from flask import Flask, request, render_template, redirect, url_for, jsonify
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader

# Flask app
app = Flask(__name__)

# Environment variables (these will be set in Render)
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")
MONGODB_URI = os.environ.get("MONGODB_URI")

# Configure Cloudinary client
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

# MongoDB client
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["video_ai_demo"]
results_col = db["results"]

def analyze_video_local(filepath: str) -> dict:
    """
    Placeholder "AI analysis" that works on any CPU.
    It reads the file size and returns a fake score.
    Replace this with your real model later.
    """
    size_bytes = os.path.getsize(filepath)
    # Simple deterministic "score"
    score = round(min(100.0, (size_bytes / (1024 * 1024)) * 10.0), 2)  # 10 points per MB, capped at 100
    return {
        "size_bytes": size_bytes,
        "approx_megabytes": round(size_bytes / (1024 * 1024), 2),
        "simple_score": score
    }

@app.route("/", methods=["GET"])
def home():
    # Show simple upload form and last 10 results
    recent = list(results_col.find().sort("_id", -1).limit(10))
    return render_template("index.html", recent=recent)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("video")
    if not file:
        return "No file uploaded", 400

    # Upload to Cloudinary as a video resource
    upload_result = cloudinary.uploader.upload(
        file,
        resource_type="video",
        folder="test_video_ai"
    )

    secure_url = upload_result["secure_url"]
    public_id = upload_result["public_id"]

    # Download the video temporarily so we can analyze locally
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    r = requests.get(secure_url, stream=True)
    r.raise_for_status()
    with open(tmp_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    try:
        analysis = analyze_video_local(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    # Save result to MongoDB
    doc = {
        "cloudinary_public_id": public_id,
        "cloudinary_url": secure_url,
        "analysis": analysis
    }
    inserted = results_col.insert_one(doc)

    return redirect(url_for("result", id=str(inserted.inserted_id)))

from bson import ObjectId

@app.route("/result/<id>", methods=["GET"])
def result(id):
    try:
        doc = results_col.find_one({"_id": ObjectId(id)})
        if not doc:
            return "Not found", 404
        return render_template("result.html", item=doc)
    except Exception:
        return "Invalid id", 400

# Health check endpoint (Render uses this sometimes)
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# For local testing only
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

