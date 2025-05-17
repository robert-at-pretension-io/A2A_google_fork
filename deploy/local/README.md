# A2A Local Docker Deployment

This directory contains Docker Compose configuration for running the A2A demo application locally.

## Getting Started

1. **Create your environment file:**

   ```bash
   cp .env.template .env
   ```

   Edit the `.env` file and add your API keys.

2. **Start the services:**

   ```bash
   docker-compose up -d
   ```

   This will start the UI and agent services in the background.

3. **Access the UI:**

   Visit http://localhost:12000 in your browser.

4. **Register the agents:**

   In the UI, go to the "Remote Agents" tab and add the agents:
   - `agent-google-adk:10002`
   - `agent-elevenlabs-tts:10005`
   - `agent-vertex-image-gen:10006` (if using Vertex AI)
   
   Note: When running in Docker, agents register using their Docker service names, not localhost or IP addresses. This is controlled by the `A2A_SERVICE_HOST` environment variable in docker-compose.yaml.

## New Features

### Delete Functionality

The application now supports deleting agents and conversations from the UI:

- **Delete agents**: A "Delete" action is available in the agent list table. Click this action to remove an agent.
- **Delete conversations**: A "Delete" action is available in the conversation list table. Click this action to delete a conversation and all related messages and tasks.

These actions are available directly in the tables - look for the "Actions" column.

## Configuration

You can modify which agents are started by editing the `docker-compose.yaml` file. Comment out or remove any agents you don't need.

## Troubleshooting

### Network Connectivity Issues

If you see errors like "Connection refused" or "Warning: there are non-text parts in the response", check the following:

1. **Verify containers are running:**
   ```bash
   docker compose ps
   ```
   All containers should show as "running".

2. **Check container logs for errors:**
   ```bash
   docker compose logs agent-elevenlabs-tts
   ```
   Look for any startup errors or warnings.

3. **Test container connectivity:**
   From the host:
   ```bash
   curl http://localhost:10005
   ```
   Or from within the Docker network:
   ```bash
   docker exec local-ui-1 python -c "import socket; s = socket.socket(); s.connect(('agent-elevenlabs-tts', 10005)); print('Connected')"
   ```

4. **Verify agent is binding to 0.0.0.0:**
   Agents must bind to 0.0.0.0 (not localhost) to be accessible from other containers.
   This is now the default, but you can check the logs to confirm.

5. **Ensure correct ports:**
   Verify that the port numbers in docker-compose.yaml match what's in the documentation.
   
   Current port assignments:
   - Google ADK Agent: 10002
   - ElevenLabs TTS Agent: 10005
   - Vertex Image Gen Agent: 10006

## Stopping the Services

To stop all services:

```bash
docker compose down
```

To stop and remove all data (including the persistent volume):

```bash
docker compose down -v
```