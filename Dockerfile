# Use an official Python runtime as a parent image
FROM python:3.10-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=my_secret_key_placeholder

# Install system dependencies required for building Python packages
RUN apk add --update --no-cache \
    gcc \
    libc-dev \
    linux-headers \
    libffi-dev \
    make \
    openssl-dev

# Set the correct working directory for the application
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

# Ensure pip is up-to-date
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install -r requirements.txt

# List installed packages for verification (optional)
RUN pip list

# Copy the rest of the application code (including subdirectories)
COPY . .

# Install redis-cli
RUN apk add --no-cache redis

# Clean up build dependencies to reduce image size
RUN apk del gcc libc-dev linux-headers libffi-dev make openssl-dev

# Define the default command to run Gunicorn, specifying the app directory if needed
CMD ["gunicorn", "app.core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
