from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.Tasks.importer import Importer


class DummyConfig:
    def __init__(self, import_path: Path, extensions=None, clean=False):
        self._import_path = import_path
        self._extensions = extensions or []
        self._clean = clean

    def get(self, section, key, default=None):
        if section == "paths" and key == "import":
            return str(self._import_path)
        if section == "extensions" and key == "import":
            return self._extensions
        if section == "import" and key == "clean":
            return self._clean
        return default


@pytest.fixture
def setup_dir(tmp_path):
    """Sets up test directory structure with files and subfolders."""
    import_dir = tmp_path / "import"
    import_dir.mkdir()

    # Valid and invalid files
    valid_file = import_dir / "song.mp3"
    invalid_file = import_dir / "document.txt"
    valid_file.write_text("music data")
    invalid_file.write_text("text data")

    # Subdirectory
    sub_dir = import_dir / "sub"
    sub_dir.mkdir()
    sub_file = sub_dir / "nested.wav"
    sub_file.write_text("nested audio")

    return import_dir, valid_file, invalid_file, sub_file


def test_importer_finds_valid_files(setup_dir):
    import_dir, valid_file, _, _ = setup_dir
    config = DummyConfig(import_path=import_dir, extensions=[".mp3", ".wav"])
    importer = Importer(config)  # type: ignore

    importer.run()

    assert valid_file in importer.files
    assert all(isinstance(f, Path) for f in importer.files)


def test_importer_ignores_invalid_files(setup_dir):
    import_dir, _, invalid_file, _ = setup_dir
    config = DummyConfig(import_path=import_dir, extensions=[".mp3"])
    importer = Importer(config)  # type: ignore

    importer.run()

    assert invalid_file not in importer.files


def test_importer_deletes_invalid_files(setup_dir):
    import_dir, _, invalid_file, _ = setup_dir
    config = DummyConfig(import_path=import_dir, extensions=[".mp3"], clean=True)
    importer = Importer(config)  # type: ignore

    importer.run()

    assert not invalid_file.exists()


def test_importer_scans_recursively(setup_dir):
    import_dir, _, _, sub_file = setup_dir
    config = DummyConfig(import_path=import_dir, extensions=[".wav"])
    importer = Importer(config)  # type: ignore

    importer.run()

    assert sub_file in importer.files


@patch("tasks.importer.Parser")
def test_importer_invokes_parser(mock_parser_class, setup_dir):
    import_dir, valid_file, _, _ = setup_dir
    config = DummyConfig(import_path=import_dir, extensions=[".mp3"])
    importer = Importer(config)  # type: ignore

    mock_task = MagicMock()
    mock_parser_class.return_value = mock_task

    importer.run()

    mock_parser_class.assert_called_once_with(config, [valid_file])
    mock_task.start.assert_called_once()
    mock_task.wait.assert_called_once()
