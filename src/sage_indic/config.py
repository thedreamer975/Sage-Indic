"""Environment and project configuration management for SAGE-Indic."""

import os
from dataclasses import dataclass
from pathlib import Path


def find_project_root() -> Path:
    """Find the root directory of the project.

    Returns:
        Path to the project root directory.
    """
    # Navigate up from src/sage_indic to project root
    return Path(__file__).resolve().parent.parent.parent


def load_env_file(dotenv_path: Path | None = None) -> None:
    """Load key-value pairs from a .env file into os.environ if not already set.

    Args:
        dotenv_path: Optional explicit path to the .env file.
    """
    if dotenv_path is None:
        dotenv_path = find_project_root() / ".env"

    if not dotenv_path.is_file():
        return

    with open(dotenv_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val


@dataclass(frozen=True)
class Settings:
    """Core settings for SAGE-Indic runtime and experiments."""

    env: str
    log_level: str
    project_root: Path
    data_dir: Path
    configs_dir: Path
    experiments_dir: Path


def get_settings() -> Settings:
    """Load settings from environment variables with sensible defaults.

    Returns:
        A populated Settings instance.
    """
    load_env_file()

    root = find_project_root()
    env = os.getenv("SAGE_ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    data_dir = Path(os.getenv("SAGE_DATA_DIR", str(root / "data")))
    configs_dir = Path(os.getenv("SAGE_CONFIGS_DIR", str(root / "configs")))
    experiments_dir = Path(os.getenv("SAGE_EXPERIMENTS_DIR", str(root / "experiments")))

    return Settings(
        env=env,
        log_level=log_level,
        project_root=root,
        data_dir=data_dir,
        configs_dir=configs_dir,
        experiments_dir=experiments_dir,
    )
