from tests.import_test_utils import run_import_test

MODULE = 'core.models'

def test_import_module() -> None:
    run_import_test(MODULE)
