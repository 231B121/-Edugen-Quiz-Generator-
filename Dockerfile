# ==============================================================================
# Production Container Image for EDUGEN
# Compatible with Hugging Face Spaces (Port 7860), Railway, Koyeb, and Docker
# ==============================================================================

FROM python:3.10-slim

WORKDIR /app

# Ensure unbuffered logs and prevent creation of pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

# Install essential system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies in isolated layer for fast cache reuse
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose standard cloud container ports (7860 for HuggingFace, 5000 for standard)
EXPOSE 7860
EXPOSE 5000

# Start WSGI production server with dynamic port fallback
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-7860} --timeout 180 --workers 1 --threads 2"]
