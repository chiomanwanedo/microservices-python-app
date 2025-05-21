import os, gridfs, pika, json
from flask import Flask, request, send_file
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util
from bson.objectid import ObjectId
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from pymongo import MongoClient
from urllib.parse import urlparse

# 🔍 Debug: print RabbitMQ env vars at container startup
print("🐇 RABBITMQ_USER:", os.environ.get("RABBITMQ_USER"))
print("🐇 RABBITMQ_PASSWORD:", os.environ.get("RABBITMQ_PASSWORD"))
print("🐇 Connecting to:", os.environ.get("RABBITMQ_HOST"))

server = Flask(__name__)

# Flask-PyMongo setup
mongo_video = PyMongo(server, uri=os.environ.get('MONGO_URI'))
mongo_mp3 = PyMongo(server, uri=os.environ.get('MONGODB_MP3S_URI'))

# Helper to extract DB name from URI
def get_db_name(uri):
    return urlparse(uri).path[1:]  # removes leading '/'

# Use raw PyMongo clients for GridFS compatibility
mongo_video_client = MongoClient(os.environ.get('MONGO_URI'))
mongo_mp3_client = MongoClient(os.environ.get('MONGODB_MP3S_URI'))

video_db = mongo_video_client[get_db_name(os.environ.get('MONGO_URI'))]
mp3_db = mongo_mp3_client[get_db_name(os.environ.get('MONGODB_MP3S_URI'))]

# GridFS setup
fs_videos = gridfs.GridFS(video_db)
fs_mp3s = gridfs.GridFS(mp3_db)

# RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters(
    host=os.environ.get("RABBITMQ_HOST", "rabbitmq"),
    credentials=pika.PlainCredentials(
        os.environ.get("RABBITMQ_USER", "guest"),
        os.environ.get("RABBITMQ_PASSWORD", "guestpassword")
    ),
    heartbeat=0
))
channel = connection.channel()

@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)
    return token if not err else err

@server.route("/upload", methods=["POST"])
def upload():
    access_token, err = validate.token(request)
    if err:
        return err

    access_data = json.loads(access_token)
    if access_data["admin"]:
        if len(request.files) != 1:
            return "exactly 1 file required", 400

        for _, f in request.files.items():
            err = util.upload(f, fs_videos, channel, access_data)
            if err:
                return err

        return "success!", 200
    return "not authorized", 401

@server.route("/download", methods=["GET"])
def download():
    access_token, err = validate.token(request)
    if err:
        return err

    access_data = json.loads(access_token)
    if access_data["admin"]:
        fid_string = request.args.get("fid")
        if not fid_string:
            return "fid is required", 400

        try:
            out = fs_mp3s.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as e:
            print(e)
            return "internal server error", 500

    return "not authorized", 401

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=5000)
