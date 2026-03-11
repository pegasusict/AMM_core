from tests.import_test_utils import run_import_test

MODULE = 'plugins.tasks.normalizer'

def test_import_module() -> None:
    run_import_test(MODULE)
