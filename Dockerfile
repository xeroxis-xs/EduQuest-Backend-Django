# Use a Debian-based Python runtime as a parent image for better compatibility
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SECRET_KEY=your_production_secret_key

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libffi-dev \
    libssl-dev \
    make \
    && rm -rf /var/lib/apt/lists/*

# Set up application directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Verify installed packages (optional, can be removed in production)
RUN pip list

# Copy the rest of the application code
COPY . .

# Install redis-cli
RUN apt-get update && apt-get install -y --no-install-recommends redis-tools \
    && rm -rf /var/lib/apt/lists/*


# Remove build dependencies to reduce image size
RUN apt-get purge -y --auto-remove gcc libc-dev libffi-dev libssl-dev make \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for running the application
RUN addgroup --system appgroup && adduser --system appuser --ingroup appgroup

# Change ownership of the application directory
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose the port Gunicorn will run on
EXPOSE 8000

# Define the default command to run Gunicorn
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
