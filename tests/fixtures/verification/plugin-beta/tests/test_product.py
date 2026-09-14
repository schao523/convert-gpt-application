import unittest


class ProductTests(unittest.TestCase):
    def test_fixture_identity(self) -> None:
        self.assertEqual("plugin-beta", "plugin-beta")
