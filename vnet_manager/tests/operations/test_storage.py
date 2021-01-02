from unittest.mock import Mock

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.storage import check_if_lxc_storage_pool_exists, create_lxc_storage_pool, delete_lxc_storage_pool
from vnet_manager.conf import settings


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


class TestCreateLXCStoragePool(VNetTestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.storage.get_lxd_client")
        self.lxd_client.return_value = self.client
        self.check_if_lxc_storage_pool_exists = self.set_up_patch("vnet_manager.operations.storage.check_if_lxc_storage_pool_exists")
        self.check_if_lxc_storage_pool_exists.return_value = False

    def test_create_lxc_storage_pool_calls_get_lxd_client(self):
        create_lxc_storage_pool("blaap")
        self.lxd_client.assert_called_once_with()

    def test_create_lxc_storage_pool_calls_check_if_lxc_storage_pool_exists(self):
        create_lxc_storage_pool("blaap")
        self.check_if_lxc_storage_pool_exists.assert_called_once_with("blaap")

    def test_create_lxc_storage_pool_raises_runtime_error_when_storage_pool_already_exists(self):
        self.check_if_lxc_storage_pool_exists.return_value = True
        with self.assertRaises(RuntimeError):
            create_lxc_storage_pool("blaap")

    def test_create_lxc_storage_pool_calls_storage_pools(self):
        create_lxc_storage_pool("blaap", "driver")
        self.client.storage_pools.create.assert_called_once_with(
            {"name": "blaap", "driver": "driver", "config": {"size": settings.LXC_STORAGE_POOL_SIZE}}
        )


class TestDeleteLXCStoragePool(VNetTestCase):
    def setUp(self) -> None:
        self.client = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.storage.get_lxd_client")
        self.lxd_client.return_value = self.client
        self.check_if_lxc_storage_pool_exists = self.set_up_patch("vnet_manager.operations.storage.check_if_lxc_storage_pool_exists")
        self.storage_pool = Mock()
        self.client.storage_pools.get.return_value = self.storage_pool

    def test_delete_lxc_storage_pool_call_get_lxd_client(self):
        delete_lxc_storage_pool("blaap")
        self.lxd_client.assert_called_once_with()

    def test_delete_lxc_storage_pools_calls_check_if_lxc_storage_pool_exists(self):
        delete_lxc_storage_pool("blaap")
        self.check_if_lxc_storage_pool_exists.assert_called_once_with("blaap")

    def test_delete_lxc_storage_pools_does_not_call_get_lxd_client_if_storage_pools_does_not_exist(self):
        self.check_if_lxc_storage_pool_exists.return_value = False
        delete_lxc_storage_pool("blaap")
        self.assertFalse(self.lxd_client.called)

    def test_delete_lxc_storage_pools_calls_storage_pools(self):
        delete_lxc_storage_pool("blaap")
        self.client.storage_pools.get.assert_called_once_with("blaap")

    def test_delete_lxc_storage_pools_calls_delete_method(self):
        delete_lxc_storage_pool("blaap")
        self.storage_pool.delete.assert_called_once_with()
