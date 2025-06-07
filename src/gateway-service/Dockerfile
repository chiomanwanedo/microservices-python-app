FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY server.py /app/
COPY auth /app/auth
COPY auth_svc /app/auth_svc
COPY storage /app/storage

# Expose Flask port
EXPOSE 5000

# Start the service
CMD ["python", "server.py"]
