from tests.import_test_utils import run_import_test

MODULE = 'mixins.autofetch'

def test_import_module() -> None:
    run_import_test(MODULE)
