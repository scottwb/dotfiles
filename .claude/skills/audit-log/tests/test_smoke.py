"""The package imports and exposes a version. Scaffolding guard."""

import unittest

from auditlog import __version__
from auditlog import cli, cost, parse, render, resolve


class TestSmoke(unittest.TestCase):
    def test_version_is_a_string(self):
        self.assertIsInstance(__version__, str)
        self.assertTrue(__version__)

    def test_modules_import(self):
        for mod in (cli, cost, parse, render, resolve):
            self.assertTrue(hasattr(mod, "__name__"))


if __name__ == "__main__":
    unittest.main()
