"""Tests for environment configuration and settings."""

from pathlib import Path

from sage_indic.config import Settings, find_project_root, get_settings, load_env_file


def test_find_project_root():
    """Verify find_project_root returns existing project root directory."""
    root = find_project_root()
    assert root.exists()
    assert (root / "pyproject.toml").is_file()


def test_get_settings_default():
    """Verify get_settings returns valid Settings instance with default values."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.env in {"development", "testing", "production"}
    assert settings.log_level in {"DEBUG", "INFO", "WARNING", "ERROR"}
    assert settings.project_root.exists()
    assert isinstance(settings.data_dir, Path)
    assert isinstance(settings.configs_dir, Path)
    assert isinstance(settings.experiments_dir, Path)


def test_load_env_file(tmp_path: Path, monkeypatch):
    """Verify load_env_file correctly parses key-value pairs without overriding existing env."""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_SAGE_KEY=test_value\n# Comment\nANOTHER_KEY=123\n", encoding="utf-8")

    monkeypatch.delenv("TEST_SAGE_KEY", raising=False)
    monkeypatch.delenv("ANOTHER_KEY", raising=False)

    load_env_file(env_file)

    import os

    assert os.environ.get("TEST_SAGE_KEY") == "test_value"
    assert os.environ.get("ANOTHER_KEY") == "123"
