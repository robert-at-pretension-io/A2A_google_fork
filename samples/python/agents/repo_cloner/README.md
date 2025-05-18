# Git Repository Cloner Agent

This agent uses the Agent Development Kit (ADK) to create a Git repository cloning agent that is hosted as an A2A server.

This agent can clone both public and private Git repositories from GitHub, GitLab, and other Git providers. It supports various options including:

- Cloning specific branches or tags
- Shallow clones with a specific depth
- Authentication for private repositories using personal access tokens

## Prerequisites

- Python 3.9 or higher
- [UV](https://docs.astral.sh/uv/)
- Access to an LLM and API Key
- Git command-line tool installed

## Running the Agent

1. Navigate to the agent directory:
    ```bash
    cd samples/python/agents/repo_cloner
    ```
2. Create an environment file with your API key:

   ```bash
   echo "GOOGLE_API_KEY=your_api_key_here" > .env
   ```

3. Run the agent:
    ```bash
    uv run .
    ```

4. In a separate terminal, run the A2A client:
    ```
    # Connect to the agent (specify the agent URL with correct port)
    cd samples/python/hosts/cli
    uv run . --agent http://localhost:10003
    ```

## Example Usage

Once connected to the agent, you can:

1. Clone a public repository:
   ```
   Clone the repository at https://github.com/user/repo.git
   ```

2. Clone a specific branch:
   ```
   Clone https://github.com/user/repo.git with branch develop
   ```

3. Create a shallow clone:
   ```
   Clone https://github.com/user/repo.git with depth 1
   ```

4. Clone a private repository:
   ```
   Clone the private repo at https://github.com/user/repo.git using token ghp_1234567890abcdef
   ```

5. Specify a destination directory:
   ```
   Clone https://github.com/user/repo.git to /home/user/projects/repo
   ```

Note: When providing tokens for private repositories, the agent will handle them securely and never reveal them in responses.
