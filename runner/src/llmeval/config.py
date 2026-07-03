"""Parse .evalrc.yml config with environment variable substitution."""

import os
import re
import yaml
from pathlib import Path
from llmeval.models import EvalConfig


def _expand_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} with the environment variable value."""
    pattern = r'\$\{([^}]+)\}'

    def replacer(match):
        var_name = match.group(1)
        val = os.environ.get(var_name)
        if val is None:
            raise ValueError(f"Environment variable '{var_name}' is not set")
        return val

    return re.sub(pattern, replacer, value)


def _expand_dict(obj):
    """Recursively expand env vars in all string values."""
    if isinstance(obj, str):
        return _expand_env_vars(obj)
    elif isinstance(obj, dict):
        return {k: _expand_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_dict(i) for i in obj]
    return obj


def load_config(path: Path = Path(".evalrc.yml")) -> EvalConfig:
    """Load and validate an .evalrc.yml config file.

    Performs environment variable substitution for ${VAR} syntax.
    Raises FileNotFoundError if the config file doesn't exist.
    Raises ValueError if a referenced env var is not set.
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    raw = yaml.safe_load(path.read_text())
    expanded = _expand_dict(raw)
    return EvalConfig(**expanded)
