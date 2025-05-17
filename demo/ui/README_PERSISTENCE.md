# A2A Demo Persistent Storage

The A2A demo now includes persistent storage for conversations and agents. This means that your conversations and registered agents will be saved between server restarts.

## How It Works

- When you start the demo, it loads previously saved conversations and agents
- When you register a new agent, it's automatically saved to disk
- When you create a conversation or send messages, they're automatically saved to disk

## Storage Location

Data is stored in a `.a2a_storage` directory in the current working directory (where you run the demo). This directory contains JSON files with the serialized data.

## Configuration

Persistence is enabled by default. If you want to disable it, set the `A2A_PERSISTENCE` environment variable to `FALSE` before starting the demo:

```bash
export A2A_PERSISTENCE=FALSE
uv run main.py
```

## Troubleshooting

If you encounter issues with persistence, you can:

1. Delete the `.a2a_storage` directory to start fresh (this will remove all saved data)
2. Disable persistence as shown above
3. Check the console for any error messages related to loading or saving data

## Limitations

This is a simple file-based persistence implementation with some limitations:

- The entire state is saved after each operation (not optimized for high traffic)
- No compression or encryption of the stored data
- Binary data (like images or audio) is not persisted and will need to be regenerated
- Task history is not fully persisted

## Future Improvements

Future versions could include:
- Database-backed storage for better scalability
- More efficient incremental updates
- Full persistence of binary artifacts
- User accounts and multi-user support