from unittest.mock import call

from vnet_manager.conf import import_from_string
from vnet_manager.tests import VNetTestCase


class TestImportFromString(VNetTestCase):
    def setUp(self) -> None:
        self.mock_import_module = self.set_up_patch("importlib.import_module", return_value="module")

        self.mock_getattr = self.set_up_patch("vnet_manager.conf.getattr", return_value="attr")

    def test_that_method_calls_import_module_correct(self):
        import_from_string("module.class.sub", "xyz")
        expected_calls = [call("module.class")]
        self.assertEqual(expected_calls, self.mock_import_module.mock_calls)

    def test_that_method_calls_get_attr_correct(self):
        import_from_string("module.class.sub", "xyz")
        expected_calls = [call("module", "sub")]
        self.assertEqual(expected_calls, self.mock_getattr.mock_calls)

    def test_that_method_raises_importerror_if_import_module_raises_importerror(self):
        self.mock_import_module.side_effect = ImportError
        with self.assertRaises(ImportError):
            import_from_string("module.class.sub", "xyz")

    def test_that_method_raises_importerror_if_getattr_raises_attributerror(self):
        self.mock_getattr.side_effect = AttributeError
        with self.assertRaises(ImportError):
            import_from_string("module.class.sub", "xyz")
