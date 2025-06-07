import os
import json
import gridfs
import traceback
from flask import Flask, request, send_file, jsonify
from flask_pymongo import PyMongo
from flask_cors import CORS, cross_origin
from bson.objectid import ObjectId
from auth import validate
from storage import util  # ✅ contains the publish() function that talks to RabbitMQ

# Debugging environment values
print("📦 MONGODB URI:", os.environ.get("MONGODB_MP3S_URI"))
print("🐇 RABBITMQ_HOST:", os.environ.get("RABBITMQ_HOST"))
print("🐇 RABBITMQ_USER:", os.environ.get("RABBITMQ_USER"))

# Flask app initialization
server = Flask(__name__)
CORS(server)

# MongoDB connection
server.config["MONGO_URI"] = os.environ.get("MONGODB_MP3S_URI")
mongo = PyMongo(server)
fs = gridfs.GridFS(mongo.db)

# Health check route
@server.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

# ✅ Upload route that only saves video and sends message to RabbitMQ
@server.route("/upload", methods=["POST"])
@cross_origin()
def upload_file():
    access, error = validate.token(request)
    if not access:
        return jsonify({"error": error}), 401

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    try:
        f_id = fs.put(file, filename=file.filename)
        print("💾 File saved with ID:", str(f_id))
    except Exception as e:
        print("❌ GridFS put error:", str(e))
        traceback.print_exc()
        return jsonify({"error": "Failed to save file"}), 500

    try:
        util.publish({
            "video_fid": str(f_id),
            "username": access["username"],
        })
        print("📤 Message published to RabbitMQ")
    except Exception as e:
        print("❌ RabbitMQ publish error:", str(e))
        traceback.print_exc()
        return jsonify({"error": "Failed to publish message"}), 500

    return jsonify({"video_fid": str(f_id)}), 200

# File download route
@server.route("/download", methods=["GET"])
@cross_origin()
def download_file():
    fid = request.args.get("fid")
    if not fid:
        return jsonify({"error": "Missing file ID"}), 400
    try:
        out = fs.get(ObjectId(fid))
        return send_file(out, download_name=out.filename)
    except Exception as e:
        print("❌ Download error:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# Simple auth-protected route
@server.route("/protected", methods=["GET"])
@cross_origin()
def protected():
    access, error = validate.token(request)
    if not access:
        return jsonify({"error": error}), 401
    return jsonify({
        "message": "✅ Protected route accessed!",
        "user": access["username"],
        "admin": access["admin"]
    })

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000, debug=True)
