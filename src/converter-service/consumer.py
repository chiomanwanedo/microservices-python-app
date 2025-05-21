import pika, sys, os, time
from pymongo import MongoClient
import gridfs
from convert import to_mp3

def main():
    # MongoDB connections
    client = MongoClient(os.environ.get('MONGODB_URI'))
    db_videos = client.videos
    db_mp3s = client.mp3s

    # GridFS setup
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # RabbitMQ connection using environment variables
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    rabbitmq_user = os.environ.get("RABBITMQ_USER", "guest")
    rabbitmq_password = os.environ.get("RABBITMQ_PASSWORD", "guestpassword")
    queue_name = os.environ.get("VIDEO_QUEUE", "video")

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password),
            heartbeat=0
        )
    )
    channel = connection.channel()

    # ✅ Ensure the queue exists (fixes NOT_FOUND error)
    channel.queue_declare(queue=queue_name, durable=True)

    # Define callback to process messages
    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    # Start consuming from the queue
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback
    )

    print("✅ Waiting for messages, to exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
