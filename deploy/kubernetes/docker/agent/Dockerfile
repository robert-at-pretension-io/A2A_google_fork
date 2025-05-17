FROM python:3.12-slim

WORKDIR /app

# ARG for which agent to install
ARG AGENT_DIR=google_adk

# Copy the whole samples/python directory for the workspace setup
COPY samples/python/ /app/

# Install the parent package first
WORKDIR /app
RUN pip install --no-cache-dir -e .

# Set working directory to agent directory
WORKDIR /app/agents/${AGENT_DIR}

# Install agent dependencies
RUN pip install --no-cache-dir -e .

# Install required packages explicitly
RUN pip install --no-cache-dir python-dotenv click

# Expose the default port (agents use 10000+)
EXPOSE 10000-10010

# Define environment variable at build time for use in the entrypoint script
ENV AGENT_NAME=${AGENT_DIR}

# Create entrypoint script that accesses the environment variable correctly and forces 0.0.0.0 binding
RUN echo '#!/bin/bash\n\
cd /app/agents/$AGENT_NAME\n\
python __main__.py --host=0.0.0.0\n\
' > /entrypoint.sh && chmod +x /entrypoint.sh

# Command to run the agent
CMD ["/entrypoint.sh"]