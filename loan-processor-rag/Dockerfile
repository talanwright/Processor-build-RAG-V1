# Use slim Python image to keep size small
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal set)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only necessary application files
COPY simple_rag_api.py .
COPY document_extractor.py .
COPY knowledge_base ./knowledge_base

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8080

# Run the application
CMD uvicorn simple_rag_api:app --host 0.0.0.0 --port ${PORT:-8080}
