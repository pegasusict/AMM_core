from tests.import_test_utils import run_import_test

MODULE = 'core.taskmanager'

def test_import_module() -> None:
    run_import_test(MODULE)
