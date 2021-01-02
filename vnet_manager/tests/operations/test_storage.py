from unittest.mock import Mock

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.storage import check_if_lxc_storage_pool_exists


class TestCheckIfLXCStoragePoolExists(VNetTestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.storage.get_lxd_client")
        self.lxd_client.return_value = self.client

    def test_check_if_lxc_storage_pool_exists_calls_get_lxd_client(self):
        check_if_lxc_storage_pool_exists("blaap")
        self.lxd_client.assert_called_once_with()

    def test_check_if_lxc_storage_pool_exists_calls_storage_pools(self):
        check_if_lxc_storage_pool_exists("blaap")
        self.client.storage_pools.exists.assert_called_once_with("blaap")
