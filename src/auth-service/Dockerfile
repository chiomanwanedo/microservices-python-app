# Use a lightweight base image
FROM python:3.10-slim-bullseye

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies (for psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app source code
COPY . .

# Expose the port your app runs on
EXPOSE 5000

# Run the app
CMD ["python", "server.py"]
