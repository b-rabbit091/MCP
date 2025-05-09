# Step 1: Use the official Python image
FROM python:3.10-slim as builder
ENV PYTHONUNBUFFERED 1

# Step 2: Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Set work directory
WORKDIR /app

# Step 4: Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy backend source code
COPY . .

# Step 6: Expose port
EXPOSE 8000

# Step 7: Use gunicorn for production
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]