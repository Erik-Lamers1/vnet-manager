from io import StringIO
from unittest.mock import patch, Mock

from vnet_manager.utils.version import show_version
from vnet_manager.tests import VNetTestCase


class TestShowVersion(VNetTestCase):
    def setUp(self) -> None:
        self.package = Mock()
        self.package.version = 1
        self.require = self.set_up_patch("vnet_manager.utils.version.require")
        self.require.return_value = [self.package]

    @patch("sys.stdout", new_callable=StringIO)
    def test_show_version_shows_version(self, stdout):
        show_version()
        self.assertEqual(stdout.getvalue().strip(), "VNet manager version 1")
