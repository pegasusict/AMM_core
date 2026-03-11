from tests.import_test_utils import run_import_test

MODULE = 'core.processor_loop'

def test_import_module() -> None:
    run_import_test(MODULE)
