from unittest.mock import Mock

from vnet_manager.conf import settings
from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.profile import check_if_lxc_profile_exists, create_vnet_lxc_profile, delete_vnet_lxc_profile


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


class TestCreateVNetLXCProfile(VNetTestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.profile.get_lxd_client")
        self.lxd_client.return_value = self.client
        self.check_if_profile_exists = self.set_up_patch("vnet_manager.operations.profile.check_if_lxc_profile_exists")
        self.check_if_profile_exists.return_value = False

    def test_create_vnet_lxc_profile_calls_get_lxd_client(self):
        create_vnet_lxc_profile("test")
        self.lxd_client.assert_called_once_with()

    def test_create_vnet_lxc_profiles_calls_check_if_profile_exists(self):
        create_vnet_lxc_profile("test")
        self.check_if_profile_exists.assert_called_once_with("test")

    def test_create_vnet_lxc_profile_raises_runtimeerror_when_profile_already_exists(self):
        self.check_if_profile_exists.return_value = True
        with self.assertRaises(RuntimeError):
            create_vnet_lxc_profile("test")

    def test_create_vnet_lxc_profile_calls_lxd_client_profile_create(self):
        create_vnet_lxc_profile("test")
        self.client.profiles.create.assert_called_once_with(
            "test", config={}, devices={"root": {"path": "/", "pool": settings.LXC_STORAGE_POOL_NAME, "type": "disk"}}
        )


class TestDeleteVNetLXCProfile(VNetTestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.profile.get_lxd_client")
        self.lxd_client.return_value = self.client
        self.profile = Mock()
        self.profile.used_by = []
        self.client.profiles.get.return_value = self.profile
        self.check_if_profile_exists = self.set_up_patch("vnet_manager.operations.profile.check_if_lxc_profile_exists")

    def test_delete_vnet_lxc_profile_calls_check_if_profile_exists(self):
        delete_vnet_lxc_profile("test")
        self.check_if_profile_exists.assert_called_once_with("test")

    def test_delete_vnet_lxc_profile_calls_get_lxd_client(self):
        delete_vnet_lxc_profile("test")
        self.lxd_client.assert_called_once_with()

    def test_delete_vnet_lxc_profile_calls_client_profiles_get(self):
        delete_vnet_lxc_profile("test")
        self.client.profiles.get.assert_called_once_with("test")

    def test_delete_vnet_lxc_profile_raises_runtimeerror_when_profile_is_still_in_use(self):
        self.profile.used_by = ["123"]
        with self.assertRaises(RuntimeError):
            delete_vnet_lxc_profile("test")

    def test_delete_vnet_lxc_profile_calls_profile_delete_method(self):
        delete_vnet_lxc_profile("test")
        self.profile.delete.assert_called_once_with()
