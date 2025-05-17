FROM python:3.13-slim

WORKDIR /app

# Copy the whole samples directory for a2a-samples dependency
COPY samples/python/ /app/samples/

# Install the a2a-samples package first
WORKDIR /app/samples
RUN pip install --no-cache-dir -e .

# Copy the UI code
WORKDIR /app
COPY demo/ui/ /app/ui/

# Change to the UI directory
WORKDIR /app/ui

# Install dependencies explicitly
RUN pip install --no-cache-dir "mesop>=1.0.0" "fastapi>=0.115.0" "uvicorn>=0.34.0" "pydantic>=2.10.6" \
    "httpx>=0.28.1" "httpx-sse>=0.4.0" "pandas>=2.2.0" "google-genai>=1.9.0" "google-adk==0.0.3" \
    "asyncio>=3.4.3" "python-dotenv>=1.0.0"

# Create directory for persistence
RUN mkdir -p /app/ui/.a2a_storage

# Expose the default port
EXPOSE 12000

# Create entrypoint script
RUN echo '#!/bin/bash\n\
cd /app/ui\n\
exec python main.py\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Command to run the application
CMD ["/entrypoint.sh"]