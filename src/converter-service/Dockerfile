# Base image
FROM python:3.10-slim-bullseye

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Copy offline wheels directory
COPY wheelhouse/ /wheelhouse/

# Install dependencies using offline wheels
RUN pip install --no-index --find-links=/wheelhouse -r requirements.txt

# Expose service port (change if needed)
EXPOSE 5000

# Start the app
CMD ["python", "server.py"]
