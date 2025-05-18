from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import logging
from pathlib import Path
from typing import Optional, Any

from pydantic import BaseModel, Field, HttpUrl

from google.adk.tools import BaseTool, ToolContext
from google.adk.agents import Agent
from common.server.task_manager import TaskManager
from task_manager import AgentWithTaskManager

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# 1️⃣  Pydantic schemas
# --------------------------------------------------------------------------- #
class CloneRepoInput(BaseModel):
    """Arguments accepted by the clone tool."""

    repo_url: HttpUrl = Field(
        description=(
            "Full HTTPS URL of the repository, e.g. "
            "`https://github.com/user/project.git` or `https://gitlab.com/user/project.git`"
        )
    )
    branch: Optional[str] = Field(
        default=None,
        description="Optional branch, tag or commitish to checkout after clone.",
    )
    depth: Optional[int] = Field(
        default=None,
        ge=1,
        description="Shallow clone depth (implies `--no-tags --shallow-submodules`).",
    )
    dest_dir: Optional[str] = Field(
        default=None,
        description=(
            "Absolute/relative directory for the clone. If omitted a temp dir is used "
            "and *persisted* so the caller can inspect it later."
        ),
    )
    token: Optional[str] = Field(
        default=None,
        description="Personal/Deploy access token for private repos.",
    )
    username_hint: Optional[str] = Field(
        default=None,
        description="Username to pair with the token (defaults to host‑specific value).",
    )


class CloneRepoOutput(BaseModel):
    """Result returned by the clone tool."""

    success: bool = Field(description="True if cloning succeeded.")
    message: str = Field(description="Human‑readable description of the result.")
    cloned_path: Optional[str] = Field(
        default=None, description="Absolute path of the new repository directory."
    )


# --------------------------------------------------------------------------- #
# 2️⃣  Helper utilities
# --------------------------------------------------------------------------- #

def _ensure_git_exists() -> None:
    """Raise FileNotFoundError if the git executable is missing."""

    from shutil import which

    if which("git") is None:
        raise FileNotFoundError("`git` executable not found in PATH.")


def _logger(ctx: ToolContext | None):
    """Return either ADK's tool logger or a noop fallback printing to stderr."""

    if ctx and getattr(ctx, "logger", None):
        return ctx.logger  # pragma: no cover

    class _Dummy:
        def _log(self, lvl: str, msg: str, *a):
            print(f"[{lvl}] {msg % a if a else msg}", file=sys.stderr)

        info = debug = warning = error = _log

    return _Dummy()


# --------------------------------------------------------------------------- #
# 3️⃣  Tool implementation
# --------------------------------------------------------------------------- #
class CloneRepoTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="clone_repo",
            description=(
                "Clone a public or private Git repository. Supports optional branch, depth, "
                "destination directory and token‑based auth (GitHub, GitLab)."
            )
        )

    async def run_async(
        self,
        *,
        args: CloneRepoInput,
        tool_context: ToolContext,  # ADK injects this
    ) -> CloneRepoOutput:
        log = _logger(tool_context)

        try:
            _ensure_git_exists()
        except FileNotFoundError as exc:
            log.error("%s", exc)
            return CloneRepoOutput(success=False, message=str(exc))

        # ------ destination dir --------------------------------------------------------- #
        tmp_holder: Optional[tempfile.TemporaryDirectory] = None
        if args.dest_dir:
            dest_path = Path(args.dest_dir).expanduser().resolve()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            tmp_holder = tempfile.TemporaryDirectory(prefix="adk_clone_")
            dest_path = Path(tmp_holder.name) / "repo"  # clone into child folder
            dest_path.parent.mkdir(parents=True, exist_ok=True)

        # ------ credentials ------------------------------------------------------------- #
        env = os.environ.copy()
        cred_file: Optional[Path] = None
        if args.token:
            username = (
                args.username_hint
                or ("x-access-token" if "github.com" in args.repo_url.host else "oauth2")
            )
            cred_line = f"https://{username}:{args.token}@{args.repo_url.host}\n"

            # use ADK tmp dir if provided, else system tmp
            base_tmp = (
                Path(getattr(tool_context, "tmp_dir", tempfile.gettempdir()))
                if tool_context
                else Path(tempfile.gettempdir())
            )
            cred_file = base_tmp / f"git‑cred‑{os.urandom(6).hex()}"
            cred_file.write_text(cred_line)
            os.chmod(cred_file, 0o600)

            env |= {
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_ASKPASS": "echo",  # some git versions still honour this
                "GIT_CREDENTIAL_HELPER": f"store --file={cred_file}",
            }
            log.debug("Created one‑shot credential file %s", cred_file)

        # ------ build command ----------------------------------------------------------- #
        cmd: list[str] = ["git", "clone"]
        if args.branch:
            cmd += ["--branch", args.branch]
        if args.depth:
            cmd += ["--depth", str(args.depth), "--shallow-submodules", "--no-tags"]
        cmd += [str(args.repo_url), str(dest_path)]

        log.info("Executing: %s", " ".join(map(str, cmd)))

        # ------ run --------------------------------------------------------------------- #
        try:
            completed = subprocess.run(
                cmd,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )
            if completed.stdout.strip():
                log.debug("stdout: %s", completed.stdout.strip())
            if completed.stderr.strip():
                log.debug("stderr: %s", completed.stderr.strip())

            # persist temp dir
            if tmp_holder:
                tmp_holder._finalizer.detach()  # pylint: disable=protected-access
                log.debug("Persisted temporary directory %s", dest_path.parent)

            return CloneRepoOutput(
                success=True,
                message=f"Repository cloned to {dest_path}",
                cloned_path=str(dest_path),
            )

        except subprocess.CalledProcessError as exc:
            log.error("Clone failed: %s", exc.stderr.strip() if exc.stderr else exc)
            return CloneRepoOutput(success=False, message=f"git clone failed: {exc.stderr.strip()}")
        finally:
            if cred_file and cred_file.exists():
                try:
                    cred_file.unlink(missing_ok=True)
                    log.debug("Removed credential file %s", cred_file)
                except OSError:
                    log.warning("Could not delete credential file %s", cred_file)


# --------------------------------------------------------------------------- #
# 4️⃣  Agent Class
# --------------------------------------------------------------------------- #
class RepoCloneAgent(AgentWithTaskManager):
    """An agent that handles Git repository cloning."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        self._agent = repo_cloner_agent
        self._user_id = 'remote_agent'
        self._runner = self._build_runner()

    def get_processing_message(self) -> str:
        return 'Processing the repository cloning request...'
    
    def invoke(self, query, session_id) -> dict:
        """Process a user query and return a response.
        
        Args:
            query: The text query from the user
            session_id: Unique ID for the conversation
            
        Returns:
            Dict with response data
        """
        try:
            from google.adk.types import Content, Part
        except ImportError:
            # Fallback for ADK versions that have different import structure
            from google.adk.typed_model import Content, Part
        
        session = self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        content = Content(
            role='user', parts=[Part.from_text(text=query)]
        )
        if session is None:
            session = self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )
        events = list(
            self._runner.run(
                user_id=self._user_id,
                session_id=session.id,
                new_message=content,
            )
        )
        if not events or not events[-1].content or not events[-1].content.parts:
            return {"text": "No response from the repository cloning agent."}
        
        response_text = '\n'.join([p.text for p in events[-1].content.parts if p.text])
        return {"text": response_text}
        
    def _build_runner(self):
        from google.adk.runners import Runner
        from google.adk.artifacts import InMemoryArtifactService
        from google.adk.sessions import InMemorySessionService
        from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
        
        return Runner(
            app_name=self._agent.name,
            agent=self._agent,
            artifact_service=InMemoryArtifactService(),
            session_service=InMemorySessionService(),
            memory_service=InMemoryMemoryService(),
        )


# --------------------------------------------------------------------------- #
# 5️⃣  Agent definition
# --------------------------------------------------------------------------- #
# Create the tool instance using the explicitly initialized BaseTool
clone_repo_tool = CloneRepoTool()

repo_cloner_agent = Agent(
    name="git_repo_cloner",
    model="gemini-2.0-flash-001",  # Using the same model as the reimbursement agent
    instruction=(
        "You are a coding assistant who can clone public or private Git repositories. "
        "When the user asks to clone, prepare a `clone_repo` tool call with `repo_url`, "
        "optional `branch`, `depth`, `dest_dir`, and if provided a `token`. Never reveal "
        "tokens in your responses. After the tool returns, summarise the result and give "
        "the absolute path if cloning succeeded."
    ),
    tools=[clone_repo_tool],
)
