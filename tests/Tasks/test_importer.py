"""Test suite to test all capabilities of the importer Task"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock
from Tasks.importer import Importer
from Enums import TaskType


@pytest.fixture
def mock_config(tmp_path):
    config = MagicMock()
    config.get_path.return_value = str(tmp_path)
    config.get.side_effect = lambda section, key, default=None: {("extensions", "import"): [".mp3", ".flac"], ("import", "clean"): False}.get(
        (section, key), default
    )
    return config


@pytest.fixture
def sample_files(tmp_path):
    (tmp_path / "keep.mp3").write_text("audio file 1")
    (tmp_path / "skip.txt").write_text("text file")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "keep.flac").write_text("audio file 2")
    return tmp_path


def test_importer_collects_files_correctly(mock_config, sample_files):
    importer = Importer(config=mock_config, dry_run=True)
    importer.run()

    collected = sorted([f.name for f in importer.files])
    assert "keep.mp3" in collected
    assert "keep.flac" in collected
    assert "skip.txt" not in collected


def test_importer_does_not_delete_in_dry_run(mock_config, sample_files, caplog):
    mock_config.get.side_effect = lambda section, key, default=None: {("extensions", "import"): [".mp3"], ("import", "clean"): True}.get(
        (section, key), default
    )

    importer = Importer(config=mock_config, dry_run=True)
    importer.run()

    log = caplog.text
    assert "[Dry-run] Would remove" in log
    assert (sample_files / "skip.txt").exists()


def test_importer_removes_files_when_not_dry(mock_config, sample_files):
    mock_config.get.side_effect = lambda section, key, default=None: {("extensions", "import"): [".mp3"], ("import", "clean"): True}.get(
        (section, key), default
    )

    importer = Importer(config=mock_config, dry_run=False)
    importer.run()

    assert not (sample_files / "skip.txt").exists()


def test_importer_invokes_parser_when_not_dry_run(mock_config, sample_files):
    mock_parser = MagicMock()
    mock_task_manager = MagicMock()
    mock_task_manager().start_task = MagicMock()

    importer = Importer(
        config=mock_config,
        task_manager_class=mock_task_manager,
        parser_class=mock_parser,
        dry_run=False,
    )
    importer.run()

    mock_task_manager().start_task.assert_called_once()
    args, kwargs = mock_task_manager().start_task.call_args
    assert args[0] is mock_parser
    assert args[1] == TaskType.PARSER
    assert isinstance(args[2], list)
    assert all(isinstance(p, Path) for p in args[2])


def test_importer_does_not_invoke_parser_in_dry_run(mock_config, sample_files):
    mock_parser = MagicMock()
    mock_task_manager = MagicMock()

    importer = Importer(
        config=mock_config,
        task_manager_class=mock_task_manager,
        parser_class=mock_parser,
        dry_run=True,
    )
    importer.run()

    mock_task_manager().start_task.assert_not_called()


def test_base_path_does_not_exist_logs_error(mock_config, caplog):
    mock_config.get_path.return_value = "/nonexistent"
    importer = Importer(config=mock_config, dry_run=True)
    importer.run()

    assert "does not exist" in caplog.text.lower()
