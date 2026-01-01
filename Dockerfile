FROM python:3.10-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY scripts ./scripts

# Create runtime directories
RUN mkdir -p /app/instance /app/logs

# Expose Flask port
EXPOSE 5000

# Run the app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]
