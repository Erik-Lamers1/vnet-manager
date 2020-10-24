from unittest.mock import Mock

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.profile import check_if_lxc_profile_exists


class TestCheckIfLXCProfileExists(VNetTestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.profile.get_lxd_client")
        self.lxd_client.return_value = self.client

    def test_check_if_lxc_profile_exists_calls_get_lxc_client(self):
        check_if_lxc_profile_exists("blaap")
        self.lxd_client.assert_called_once_with()

    def test_check_if_lxc_profile_exists_calls_client_profile(self):
        check_if_lxc_profile_exists("blaap")
        self.client.profiles.exists.assert_called_once_with("blaap")
