import json
import shutil
import tempfile
from pathlib import Path
import pytest

pytest.importorskip("pydantic")

from Singletons.config import Config, AppConfig
from config.defaults import DEFAULT_CONFIG, CONFIG_VERSION
from config.manager import AsyncConfigManager


@pytest.fixture(autouse=True)
def reset_config_singleton():
    AsyncConfigManager._instance = None
    yield
    AsyncConfigManager._instance = None


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "config.json"
    with Path.open(config_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    yield config_path
    shutil.rmtree(temp_dir)


def test_load_default_when_file_missing(tmp_path):
    """Config loads defaults if file does not exist."""
    config = Config(config_file=tmp_path / "missing.json")
    assert isinstance(config.model, AppConfig)
    assert config.model.general.clean is True


def test_valid_config_load(temp_config_file):
    """Config loads and validates valid config.json."""
    config = Config(config_file=temp_config_file)
    assert config.model.version in {"1.0", "1.1"}
    assert config.model.paths.base.startswith("/alpha")


def test_invalid_json_fallback(tmp_path):
    """Invalid JSON triggers fallback to DEFAULT_CONFIG."""
    broken_file = tmp_path / "config.json"
    broken_file.write_text("{ this is : not json }")
    config = Config(config_file=broken_file)
    assert config.model.version in {CONFIG_VERSION, "1.1"}


def test_config_reload_sync(temp_config_file):
    """Explicit reload_sync updates config when file changes."""
    config = Config(config_file=temp_config_file)

    with Path.open(temp_config_file, "w", encoding="utf-8") as f:
        new_config = dict(DEFAULT_CONFIG)
        new_config["version"] = "9.99"
        json.dump(new_config, f, indent=4)

    config._manager.reload_sync()
    assert config.model.version != DEFAULT_CONFIG["version"]


def test_config_stop_watching(temp_config_file):
    """Watcher stops cleanly without error."""
    config = Config(config_file=temp_config_file)
    config.stop_watching()  # Should stop the observer thread safely
