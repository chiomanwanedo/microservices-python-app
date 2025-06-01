def upload(f, fs, channel, access):
    try:
        file_id = fs.put(f, filename=f.filename, metadata={"username": access["username"]})
        message = {
            "video_fid": str(file_id),
            "username": access["username"]
        }
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        return file_id, None
    except Exception as err:
        print("Upload error:", err)
        return None, ("internal server error", 500)
