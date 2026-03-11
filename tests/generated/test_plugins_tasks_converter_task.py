from tests.import_test_utils import run_import_test

MODULE = 'plugins.tasks.converter_task'

def test_import_module() -> None:
    run_import_test(MODULE)
