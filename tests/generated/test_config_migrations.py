from tests.import_test_utils import run_import_test

MODULE = 'config.migrations'

def test_import_module() -> None:
    run_import_test(MODULE)
