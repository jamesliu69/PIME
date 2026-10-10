import os
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
PYTHON_DIR = os.path.join(ROOT, "python")
CHECJ_DIR = os.path.join(PYTHON_DIR, "input_methods", "checj")
for path in (PYTHON_DIR, CHECJ_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)


class FakeClient(object):
    """Minimal stand-in for the RPC client used by the text service."""

    isUiLess = False
    isWindows8Above = True
    isMetroApp = False
    isConsole = False

    def __getattr__(self, name):
        def noop(*args, **kwargs):
            pass
        return noop


class MenuTogglePersistenceTests(unittest.TestCase):
    """The `` `M `` -> 功能開關 toggles must be written back to config.json.

    Otherwise the switch only lives in memory: it is lost on the next IME
    restart and silently reverted by applyConfig() as soon as the config file
    changes, which makes the 聯想字詞 (phrase association) feature look broken.
    """

    def setUp(self):
        import checj_ime
        from cinbase.config import CinBaseConfig

        self.checj_ime = checj_ime
        self.config_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.config_dir.cleanup)
        config_dir = self.config_dir.name
        # patch the class (not the shared instance), otherwise the lambda would be
        # copied into the deep-copied config and lose its binding
        self.patcher = mock.patch.object(type(CinBaseConfig), "getConfigDir",
                                         lambda self: config_dir)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def make_service(self):
        service = self.checj_ime.CheCJTextService(FakeClient())
        service.smenuitems = ["fullShapeSymbols", "easySymbolsWithShift", "autoClearCompositionChar",
                              "playSoundWhenNonCand", "showPhrase", "sortByPhrase", "supportWildcard",
                              "imeReverseLookup", "homophoneQuery"]
        return service

    def config_file(self):
        return os.path.join(self.config_dir.name, "config.json")

    def test_show_phrase_toggle_is_saved_and_survives_reload(self):
        service = self.make_service()
        self.assertFalse(service.showPhrase)

        service.cinbase.onMenuCommand(service, service.smenuitems.index("showPhrase"), 1)

        self.assertTrue(service.showPhrase)
        self.assertTrue(service.cfg.showPhrase)

        with open(self.config_file(), encoding="utf-8") as f:
            self.assertIn('"showPhrase": true', f.read())

        # a config reload must not revert the user's choice
        service.cinbase.applyConfig(service)
        self.assertTrue(service.showPhrase)

    def test_toggle_is_applied_to_the_next_service_instance(self):
        service = self.make_service()
        service.cinbase.onMenuCommand(service, service.smenuitems.index("showPhrase"), 1)

        new_service = self.make_service()
        self.assertTrue(new_service.showPhrase)


if __name__ == "__main__":
    unittest.main()
