# repo_cloner_agent.py
from __future__ import annotations

"""ADK tool + agent that can clone public *or* private Git/GitLab repositories.

Key improvements over previous draft
------------------------------------
* Early check that the `git` executable exists.
* Pathlib everywhere for consistency.
* Token‑auth username automatically chosen based on host (GitHub ⇒ ``x-access-token``,
  GitLab ⇒ ``oauth2``; overridable via ``username_hint``).
* Uses a one‑shot *credential‑store* helper so the PAT never appears on the command line
  (and the helper file is shredded immediately afterwards).
* Safer temporary‑directory handling – always clone into a child of the temp dir so we
  can detach the finaliser without leaking a random prefix.
* Fallback logger so the tool is still usable when ADK does not inject ``tool_context``.
* Strict Pydantic validation + richer doc‑strings.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl

try:
    from google.adk.tools import BaseTool, ToolContext  # type: ignore
    from google.adk.agents import Agent  # type: ignore
except ImportError as exc:  # graceful msg if ADK not installed
    sys.exit("google‑adk is required for this script → pip install google‑cloud‑aiplatform")

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
    name = "clone_repo"
    description = (
        "Clone a public or private Git repository. Supports optional branch, depth, "
        "destination directory and token‑based auth (GitHub, GitLab)."
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
# 4️⃣  Agent wiring
# --------------------------------------------------------------------------- #
repo_cloner_agent = Agent(
    name="git_repo_cloner",
    model="gemini-2.0-flash-001",
    instruction=(
        "You are a coding assistant who can clone public or private Git repositories. "
        "When the user asks to clone, prepare a `clone_repo` tool call with `repo_url`, "
        "optional `branch`, `depth`, `dest_dir`, and if provided a `token`. Never reveal "
        "tokens in your responses. After the tool returns, summarise the result and give "
        "the absolute path if cloning succeeded."
    ),
    tools=[CloneRepoTool()],
)


# --------------------------------------------------------------------------- #
# 5️⃣  CLI test harness (optional) – run `python repo_cloner_agent.py`
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Quick CLI test for the clone tool")
    parser.add_argument("url", help="Repository HTTPS URL")
    parser.add_argument("--branch")
    parser.add_argument("--depth", type=int)
    parser.add_argument("--dest-dir")
    parser.add_argument("--token")
    parser.add_argument("--username-hint")
    args_ns = parser.parse_args()

    request = f"Clone {args_ns.url}"
    if args_ns.branch:
        request += f" on branch {args_ns.branch}"
    if args_ns.depth:
        request += f" with depth {args_ns.depth}"
    if args_ns.dest_dir:
        request += f" into {args_ns.dest_dir}"
    if args_ns.token:
        request += " using this token: <REDACTED>"

    print("USER:", request)
    response = repo_cloner_agent.chat(request)  # type: ignore
    print("ASSISTANT:", response)
