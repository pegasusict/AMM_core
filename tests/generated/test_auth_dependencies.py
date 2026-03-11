from tests.import_test_utils import run_import_test

MODULE = 'auth.dependencies'

def test_import_module() -> None:
    run_import_test(MODULE)
