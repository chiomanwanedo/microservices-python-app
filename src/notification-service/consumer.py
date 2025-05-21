import pika, sys, os, time
import smtplib
from email.message import EmailMessage

def main():
    # ✅ Load RabbitMQ credentials from environment
    rabbitmq_host = os.environ.get("RABBITMQ_HOST", "rabbitmq")
    rabbitmq_user = os.environ.get("RABBITMQ_USER", "guest")
    rabbitmq_password = os.environ.get("RABBITMQ_PASSWORD", "guestpassword")

    # ✅ Connect to RabbitMQ with credentials
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=rabbitmq_host,
            credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_password),
            heartbeat=0
        )
    )
    channel = connection.channel()

    # ✅ Ensure queue exists (optional but safe)
    channel.queue_declare(queue="video", durable=True)

    # Define the email-sending function
    def send_email(body):
        try:
            email_address = os.environ.get("EMAIL_USER")
            email_password = os.environ.get("EMAIL_PASSWORD")

            msg = EmailMessage()
            msg["Subject"] = "Video Conversion Complete"
            msg["From"] = email_address
            msg["To"] = email_address  # or use body/email in message
            msg.set_content(f"Your video was successfully converted to audio.\n\n{body.decode()}")

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(email_address, email_password)
                smtp.send_message(msg)

            print("✅ Email sent.")
        except Exception as e:
            print("❌ Email failed:", e)

    # RabbitMQ message callback
    def callback(ch, method, properties, body):
        print("📩 Received notification message...")
        send_email(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    # Start listening
    channel.basic_consume(queue="video", on_message_callback=callback)

    print("✅ Notification service started. Listening for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("⛔ Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
