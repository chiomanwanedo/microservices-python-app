import os, json, gridfs, pymongo
from bson.objectid import ObjectId
import pika
from convert import to_mp3  # your module that does conversion
import traceback

# 🌍 MongoDB connection
client = pymongo.MongoClient(os.environ.get("MONGO_URI"))  # e.g. mongodb://mongoUser:mongoPass@mongodb:27017/videos?authSource=admin
db = client["videos"]
fs_videos = gridfs.GridFS(db, collection="fs")
fs_mp3s = gridfs.GridFS(db, collection="mp3s")

# 🔐 RabbitMQ credentials
credentials = pika.PlainCredentials(
    username=os.environ.get("RABBITMQ_USER"),
    password=os.environ.get("RABBITMQ_PASSWORD")
)

# 🐇 Debug: Print connection settings
print("🐇 Connecting to RabbitMQ at", os.environ.get("RABBITMQ_HOST"), "on port", os.environ.get("RABBITMQ_PORT", 5672))
print("🧑 User:", os.environ.get("RABBITMQ_USER"))
print("🔐 VHost: /")

# ✅ RabbitMQ connection
params = pika.ConnectionParameters(
    host=os.environ.get("RABBITMQ_HOST"),
    port=int(os.environ.get("RABBITMQ_PORT", 5672)),
    virtual_host="/",
    credentials=credentials
)

try:
    connection = pika.BlockingConnection(params)
    print("📡 Connected to RabbitMQ successfully")
except Exception as conn_err:
    print("❌ Failed to connect to RabbitMQ:", conn_err)
    traceback.print_exc()
    exit(1)

channel = connection.channel()
channel.queue_declare(queue="video", durable=True)
channel.basic_qos(prefetch_count=1)  # ✅ Fair message dispatch

def callback(ch, method, properties, body):
    print("📩 Received message")
    try:
        message = json.loads(body)
        video_fid = message["video_fid"]

        try:
            out = fs_videos.get(ObjectId(video_fid))
        except gridfs.errors.NoFile:
            print(f"⚠️ File not found for ID: {video_fid}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        print(f"🎬 Starting conversion for: {video_fid}")
        err = to_mp3.start(message, fs_videos, fs_mp3s, ch)
        if err:
            raise Exception("Conversion failed")

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        traceback.print_exc()
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    try:
        print("✅ Waiting for messages, to exit press CTRL+C")
        channel.basic_consume(queue="video", on_message_callback=callback)
        channel.start_consuming()
    except Exception as e:
        print("❌ start_consuming() crashed:", str(e))
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
