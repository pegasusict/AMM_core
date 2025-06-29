import time
import json
import shutil
import tempfile
from pathlib import Path
import pytest
from Singletons.config import Config, AppConfig, DEFAULT_CONFIG, CONFIG_VERSION


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    temp_dir = tempfile.mkdtemp()
    config_path = Path(temp_dir) / "config.json"
    with Path.open(config_path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    yield config_path
    shutil.rmtree(temp_dir)


def test_load_default_when_file_missing():
    """Config loads defaults if file does not exist."""
    config = Config(config_file=Path("/nonexistent/config.json"))
    assert isinstance(config.config, AppConfig)
    assert config.config.general.clean is True


def test_valid_config_load(temp_config_file):
    """Config loads and validates valid config.json."""
    config = Config(config_file=temp_config_file)
    assert config.config.version == "1.0"
    assert config.config.paths.base.startswith("/alpha")


def test_invalid_json_fallback(tmp_path):
    """Invalid JSON triggers fallback to DEFAULT_CONFIG."""
    broken_file = tmp_path / "config.json"
    broken_file.write_text("{ this is : not json }")
    config = Config(config_file=broken_file)
    assert config.config.version == CONFIG_VERSION


def test_config_auto_reload(temp_config_file):
    """Changing config.json should trigger reload."""
    config = Config(config_file=temp_config_file)
    # original_version = config.config.version

    # Modify config file
    with Path.open(temp_config_file, "w", encoding="utf-8") as f:
        new_config = dict(DEFAULT_CONFIG)
        new_config["version"] = "9.99"
        json.dump(new_config, f, indent=4)

    time.sleep(1.5)  # Wait for watchdog to pick up the change

    assert config.config.version == "9.99"


def test_config_stop_watching(temp_config_file):
    """Watcher stops cleanly without error."""
    config = Config(config_file=temp_config_file)
    config.stop_watching()  # Should stop the observer thread safely
