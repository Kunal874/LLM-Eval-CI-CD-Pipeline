"""Typer CLI entry point for the LLM eval runner."""

import asyncio
import subprocess
import typer
from pathlib import Path
from llmeval.config import load_config
from llmeval.runner import run_eval

app = typer.Typer(help="LLM Eval — evaluate your LLM pipeline on every commit")


def _get_git_info() -> dict:
    """Extract git metadata if available. Fails silently."""
    try:
        commit = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
        branch = (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
        return {"commit_hash": commit, "branch": branch}
    except Exception:
        return {}


@app.command()
def run(
    config: Path = typer.Option(
        Path(".evalrc.yml"),
        "--config",
        "-c",
        help="Path to .evalrc.yml config file",
    ),
    ci: bool = typer.Option(
        False,
        "--ci",
        help="Running in CI mode (sets triggered_by=github_actions)",
    ),
):
    """Run the evaluation pipeline."""
    try:
        cfg = load_config(config)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Config error: {e}", err=True)
        raise typer.Exit(1)

    git_info = _get_git_info()
    git_info["triggered_by"] = "github_actions" if ci else "cli"

    passed = asyncio.run(run_eval(cfg, git_info))

    raise typer.Exit(0 if passed else 1)


if __name__ == "__main__":
    app()
