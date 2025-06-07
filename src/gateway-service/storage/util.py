# storage/util.py

import os
import json
import pika

# ✅ Set up RabbitMQ connection parameters using env vars
credentials = pika.PlainCredentials(
    os.environ.get("RABBITMQ_USER"),
    os.environ.get("RABBITMQ_PASSWORD")
)

parameters = pika.ConnectionParameters(
    host=os.environ.get("RABBITMQ_HOST"),
    credentials=credentials
)

# ✅ Create and reuse a single connection/channel (or make it per-call if needed)
connection = pika.BlockingConnection(parameters)
channel = connection.channel()
channel.queue_declare(queue="video", durable=True)  # Ensure queue exists

def publish(message: dict):
    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",  # Queue name
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        print(f"📤 Published message to RabbitMQ: {message}")
    except Exception as e:
        print(f"❌ RabbitMQ publish error: {e}")
