# Using Tilt with A2A Demo

[Tilt](https://tilt.dev/) is a development tool that simplifies microservice development by providing a unified interface for building, deploying, and monitoring multiple services.

## Prerequisites

1. Install Tilt:
   ```bash
   # macOS
   brew install tilt-dev/tap/tilt

   # Linux
   curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
   ```

2. Make sure Docker is running

3. Environment variables are set up in `/deploy/local/.env`

## Running with Tilt

1. From the project root, run:
   ```bash
   tilt up
   ```

2. Tilt will:
   - Build all required Docker images
   - Start the A2A UI and all agents
   - Open the UI in your browser automatically (http://localhost:12001)
   - Display logs and status for all services
   - Watch for file changes to trigger rebuilds

3. To stop all services:
   ```bash
   tilt down
   ```

## Tilt Features for A2A Demo

- **Web UI**: View logs, statuses, and resource utilization for all services in a web interface (http://localhost:10350)
- **Live Updates**: Changes to source code or configuration automatically trigger rebuilds and restarts
- **Resource Dependencies**: Services are started in the correct order
- **Unified Logs**: View all service logs in a single interface
- **Agent Info**: Shows the addresses to use when registering agents in the UI

## Agent Discovery and Networking

### Service Names in Docker/Tilt Environment

When running with Tilt, agents register themselves using their Docker service names (not IP addresses or localhost). This ensures proper service discovery within the Docker network.

The agent URLs in the Docker environment are:
- `http://agent-google-adk:10002/`
- `http://agent-elevenlabs-tts:10005/`
- `http://agent-vertex-image-gen:10006/`

This is controlled by the `A2A_SERVICE_HOST` environment variable which is set in the docker-compose.yaml file.

### Registering Agents

After the UI and agents are running, go to the "Remote Agents" tab in the UI and add:
- agent-google-adk:10002
- agent-elevenlabs-tts:10005
- agent-vertex-image-gen:10006

**Note:** The agent registration process should find the agents at their Docker service names, not at localhost or IP addresses.

## Customizing Tilt Behavior

Edit the `Tiltfile` to customize the development workflow:

- Add more agents by extending the docker-compose.yaml and adding corresponding resources to the Tiltfile
- Modify resource dependencies to control startup order
- Add custom commands or health checks
- Configure file watching for live updates