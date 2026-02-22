# Use official Python 3.11 image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for Pillow and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create all necessary upload directories
RUN mkdir -p uploads/materials/images \
    uploads/materials/pdfs \
    uploads/materials/ppts \
    uploads/materials/csvs \
    uploads/materials/texts \
    uploads/solutions/images \
    uploads/solutions/documents \
    uploads/solutions/texts \
    uploads/tasks/images \
    uploads/tasks/pdfs

# Set proper permissions for uploads
RUN chmod -R 755 uploads

# Expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD gunicorn --bind 0.0.0.0:5000 app:app