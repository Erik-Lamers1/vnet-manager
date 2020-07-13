from unittest.mock import Mock

from vnet_manager.conf import Settings
from vnet_manager.tests import VNetTestCase


class TestSettings(VNetTestCase):
    def setUp(self) -> None:
        self.mod = Mock(lower=123, UPPER=456, MiXeD=789)
        self.mock_importlib = self.set_up_patch("importlib.import_module", return_value=self.mod)
        self.mock_settings = Settings("module.class.sub")

    def test_that_init_only_sets_upper_variables(self):
        self.assertListEqual(["UPPER"], self.mock_settings.__iter__())

    def test_that_getitem_returns_value_of_setting(self):
        self.assertEqual(self.mock_settings["UPPER"], 456)

    def test_that_iter_returns_iterable(self):
        self.assertIsInstance(self.mock_settings.__iter__(), list)

    def test_that_len_returns_correct_length_of_all_settings(self):
        self.assertEqual(1, len(self.mock_settings))
