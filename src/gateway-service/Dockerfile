FROM python:3.10-slim-bullseye

# Install only what you need, and clean up after
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev python3-dev \
 && pip install --no-cache-dir --upgrade pip \
 && apt-get purge -y gcc python3-dev \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app
COPY . .

# Clean pycache just in case
RUN rm -rf __pycache__ *.pyc

EXPOSE 5000
CMD ["python", "server.py"]
