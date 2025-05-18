# Agent2Agent (A2A) Protocol

![A2A Banner](docs/assets/a2a-banner.png)
[![Apache License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

**An open protocol enabling communication and interoperability between opaque agentic applications.**

The Agent2Agent (A2A) protocol addresses a critical challenge in the AI landscape: enabling gen AI agents, built on diverse frameworks by different companies running on separate servers, to communicate and collaborate effectively - as agents, not just as tools. A2A aims to provide a common language for agents, fostering a more interconnected, powerful, and innovative AI ecosystem.

With A2A, agents can:

- Discover each other's capabilities.
- Negotiate interaction modalities (text, forms, media).
- Securely collaborate on long running tasks.
- Operate without exposing their internal state, memory, or tools.

## See A2A in Action

Watch [this demo video](https://storage.googleapis.com/gweb-developer-goog-blog-assets/original_videos/A2A_demo_v4.mp4) to see how A2A enables seamless communication between different agent frameworks.

## Why A2A?

As AI agents become more prevalent, their ability to interoperate is crucial for building complex, multi-functional applications. A2A aims to:

- **Break Down Silos:** Connect agents across different ecosystems.
- **Enable Complex Collaboration:** Allow specialized agents to work together on tasks that a single agent cannot handle alone.
- **Promote Open Standards:** Foster a community-driven approach to agent communication, encouraging innovation and broad adoption.
- **Preserve Opacity:** Allow agents to collaborate without needing to share internal memory, proprietary logic, or specific tool implementations, enhancing security and protecting intellectual property.

### Key Features

- **Standardized Communication:** JSON-RPC 2.0 over HTTP(S).
- **Agent Discovery:** Via "Agent Cards" detailing capabilities and connection info.
- **Flexible Interaction:** Supports synchronous request/response, streaming (SSE), and asynchronous push notifications.
- **Rich Data Exchange:** Handles text, files, and structured JSON data.
- **Enterprise-Ready:** Designed with security, authentication, and observability in mind.

## Getting Started

- 📚 **Explore the Documentation:** Visit the [Agent2Agent Protocol Documentation Site](https://google.github.io/A2A/) for a complete overview, the full protocol specification, tutorials, and guides.
- 📝 **View the Specification:** [A2A Protocol Specification](https://google.github.io/A2A/specification/)
- 🐍 Use the [A2A Python SDK](https://github.com/google/a2a-python)
- 🎬 Use our [samples](/samples) to see A2A in action
  - [Multi-Agent Web App](/demo/README.md)
  - CLI ([Python](/samples/python/hosts/cli/README.md), [JS](/samples/js/README.md))
  - [Local Docker Deployment](/deploy/local/README.md)
- 🤖 **Sample Agents** - explore our [sample agent implementations](/samples/python/agents/README.md):
  - Framework Integrations:
    - [Agent Development Kit (ADK)](/samples/python/agents/google_adk/README.md)
    - [CrewAI](/samples/python/agents/crewai/README.md)
    - [LangGraph](/samples/python/agents/langgraph/README.md)
    - [LlamaIndex](/samples/python/agents/llama_index_file_chat/README.md)
    - [Marvin](/samples/python/agents/marvin/README.md)
    - [Semantic Kernel](/samples/python/agents/semantickernel/README.md)
    - [AG2 + MCP](/samples/python/agents/ag2/README.md)
    - [Genkit (JavaScript)](/samples/js/src/agents/README.md)
  - Specialized Capability Agents:
    - [Enterprise Data Agent (Gemini + Mindsdb)](/samples/python/agents/mindsdb/README.md)
    - [ElevenLabs TTS](/samples/python/agents/elevenlabs_tts/README.md)
    - [Vertex AI Image Generator](/samples/python/agents/vertex_image_gen/README.md)
    - [Git Repository Cloner](/samples/python/agents/repo_cloner/README.md)

  See the [full agent development guide](/samples/python/agents/README.md#creating-a-new-agent) for instructions on creating your own agent.

## Troubleshooting

### Common Issues

#### Docker/Network Connectivity Issues

If you're running the Docker deployment and seeing errors like "Connection refused" or warnings about "non-text parts in the response":

1. **Agent Networking:** Ensure agents bind to `0.0.0.0` (not just localhost) when running in Docker containers.
2. **Port Configuration:** Verify port mappings in `docker-compose.yaml` match the agent configuration and documentation.
3. **Agent Registration:** Make sure you're using the correct host:port combinations when registering agents in the UI.

See the [Docker deployment troubleshooting section](/deploy/local/README.md#troubleshooting) for detailed steps.

#### Agent Communication Errors

If agents are running but cannot communicate:

1. **Content Types:** Ensure the `acceptedOutputModes` in requests match the agent's capabilities.
2. **API Keys:** Verify that required API keys (like ELEVENLABS_API_KEY) are properly set in environment variables.
3. **Authentication:** Check that any required authentication is properly configured.

## Contributing

We welcome community contributions to enhance and evolve the A2A protocol!

- **Questions & Discussions:** Join our [GitHub Discussions](https://github.com/google/A2A/discussions).
- **Issues & Feedback:** Report issues or suggest improvements via [GitHub Issues](https://github.com/google/A2A/issues).
- **Contribution Guide:** See our [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute.
- **Private Feedback:** Use this [Google Form](https://goo.gle/a2a-feedback).
- **Partner Program:** Google Cloud customers can join our partner program via this [form](https://goo.gle/a2a-partner).

## What's next

### Protocol Enhancements

- **Agent Discovery:**
  - Formalize inclusion of authorization schemes and optional credentials directly within the `AgentCard`.
- **Agent Collaboration:**
  - Investigate a `QuerySkill()` method for dynamically checking unsupported or unanticipated skills.
- **Task Lifecycle & UX:**
  - Support for dynamic UX negotiation _within_ a task (e.g., agent adding audio/video mid-conversation).
- **Client Methods & Transport:**
  - Explore extending support to client-initiated methods (beyond task management).
  - Improvements to streaming reliability and push notification mechanisms.

## About

The A2A Protocol is an open-source project by Google LLC, under the [Apache License 2.0](LICENSE), and is open to contributions from the community.
