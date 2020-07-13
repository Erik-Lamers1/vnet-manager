from unittest.mock import call

from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import perform_import


class TestPerformImport(VNetTestCase):
    def setUp(self) -> None:
        self.mock_import_from_string = self.set_up_patch("vnet_manager.conf.import_from_string", return_value="imported")

    def test_perform_import_return_none_if_value_is_none(self):
        returned = perform_import(None, "abc")
        self.assertIsNone(returned)

    def test_perform_import_return_value_if_incorrect_val_passed(self):
        returned = perform_import(123, "xyz")
        self.assertEqual(returned, 123)

    def test_perform_import_return_import_result_if_single_import_is_performed(self):
        returned = perform_import("abc", "xyz")
        self.assertEqual(returned, "imported")

    def test_perform_import_return_import_result_list_if_import_list_is_performed(self):
        returned = perform_import(["a", "b", "c"], "xyz")
        self.assertListEqual(returned, ["imported", "imported", "imported"])

    def test_perform_import_that_import_from_string_is_called_once_on_string_value(self):
        perform_import("abc", "xyz")
        expected_calls = [call("abc", "xyz")]
        self.assertEqual(expected_calls, self.mock_import_from_string.mock_calls)

    def test_perform_import_that_import_from_list_is_called_for_each_element(self):
        perform_import(["a", "b", "c"], "xyz")
        expected_calls = [call("a", "xyz"), call("b", "xyz"), call("c", "xyz")]
        self.assertListEqual(expected_calls, self.mock_import_from_string.mock_calls)
