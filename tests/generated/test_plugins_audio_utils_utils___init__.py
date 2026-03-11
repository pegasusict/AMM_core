from tests.import_test_utils import run_import_test

MODULE = 'plugins.audio_utils.utils.__init__'

def test_import_module() -> None:
    run_import_test(MODULE)
