FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/media /app/staticfiles /app/static

# Copy project files
COPY . .

# Set permissions
RUN chmod -R 777 /app/media /app/staticfiles /app/static

# Expose port
EXPOSE 8000

# Run bot
CMD ["python", "manage.py", "runbot"]
