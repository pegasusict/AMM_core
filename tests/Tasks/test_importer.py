import pytest
from pathlib import Path
from unittest.mock import Mock

from Tasks.importer import ImporterConfig, DirectoryScanner, Importer

# ---------------------------------------------
# Mocks for Stack, Logger, TaskManager, Parser
# ---------------------------------------------


class MockStack:
    def __init__(self):
        self.counters = {}

    def add_counter(self, key):
        self.counters[key] = self.counters.get(key, 0) + 1


class MockLogger:
    def __init__(self):
        self.messages = {"info": [], "error": [], "warning": []}

    def info(self, msg):
        self.messages["info"].append(msg)

    def error(self, msg):
        self.messages["error"].append(msg)

    def warning(self, msg):
        self.messages["warning"].append(msg)


class MockTaskManager:
    def __init__(self):
        self.task_calls = []

    def start_task(self, parser_cls, task_type, files):
        self.task_calls.append((parser_cls, task_type, files))


class MockParser:
    pass


# ----------------------------
# ImporterConfig Tests
# ----------------------------


@pytest.mark.parametrize(
    "ext_val, expected",
    [
        ("mp3", ["mp3"]),
        (["mp3", "flac"], ["mp3", "flac"]),
        (123, []),
    ],
)
def test_importer_config_extension_parsing(ext_val, expected):
    config = Mock()
    config.get_path.return_value = "/tmp/test"
    config.get.side_effect = lambda section, key=None, default=None: {("extensions", "import"): ext_val, ("import", "clean"): True}.get(
        (section, key),  # type: ignore
        default,  # type: ignore
    )

    cfg = ImporterConfig.from_config(config, dry_run=True)
    assert cfg.base_path == Path("/tmp/test")
    assert cfg.extensions == expected
    assert cfg.clean is True
    assert cfg.dry_run is True


# ----------------------------
# DirectoryScanner Tests
# ----------------------------


def test_directory_scanner_finds_files(tmp_path):
    (tmp_path / "keep.mp3").write_text("audio")
    (tmp_path / "remove.txt").write_text("text")
    subdir = tmp_path / "sub"
    subdir.mkdir()
    (subdir / "another.mp3").write_text("audio")

    config = ImporterConfig(base_path=tmp_path, extensions=[".mp3"], clean=True, dry_run=False)
    logger = MockLogger()
    stack = MockStack()

    scanner = DirectoryScanner(config=config, logger=logger, stack=stack)
    scanner.scan(tmp_path)

    assert len(scanner.files) == 2
    assert any("remove.txt" not in f.name for f in scanner.files)
    assert "all_files" in stack.counters
    assert "removed_files" in stack.counters


def test_directory_scanner_dry_run(tmp_path):
    (tmp_path / "unwanted.docx").write_text("irrelevant")

    config = ImporterConfig(base_path=tmp_path, extensions=[".mp3"], clean=True, dry_run=True)
    logger = MockLogger()
    stack = MockStack()

    scanner = DirectoryScanner(config=config, logger=logger, stack=stack)
    scanner.scan(tmp_path)

    assert "Would remove" in logger.messages["info"][0]
    assert "removed_files" not in stack.counters


# ----------------------------
# Importer Integration Tests
# ----------------------------


def mock_config_with_exts(path, exts):
    config = Mock()
    config.get_path.return_value = path
    config.get.side_effect = lambda section, key=None, default=None: {("extensions", "import"): exts, ("import", "clean"): False}.get((section, key), default)  # type: ignore
    return config


def test_importer_run_launches_parser(tmp_path):
    file1 = tmp_path / "song.mp3"
    file1.write_text("music")

    config = mock_config_with_exts(tmp_path, [".mp3"])
    task_manager = MockTaskManager()
    parser = MockParser()

    importer = Importer(config, task_manager_class=lambda: task_manager, parser_class=parser, dry_run=False)  # type: ignore
    importer.logger = MockLogger()  # type: ignore
    importer.stack = MockStack()  # type: ignore
    importer.run()

    assert len(task_manager.task_calls) == 1
    _, _, files = task_manager.task_calls[0]
    assert file1 in files


def test_importer_dry_run_logs_files(tmp_path):
    file1 = tmp_path / "track.flac"
    file1.write_text("data")

    config = mock_config_with_exts(tmp_path, [".flac"])
    importer = Importer(config, task_manager_class=MockTaskManager, parser_class=MockParser, dry_run=True)

    logger = MockLogger()
    importer.logger = logger  # type: ignore
    importer.stack = MockStack()  # type: ignore
    importer.run()

    assert "Dry-run" in logger.messages["info"][0]
