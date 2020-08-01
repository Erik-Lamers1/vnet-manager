from unittest.mock import MagicMock
from pylxd.exceptions import NotFound

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.image import check_if_lxc_image_exists, create_lxc_image_from_container, destroy_lxc_image


class TestCheckIfLXCImageExists(VNetTestCase):
    def setUp(self) -> None:
        self.client = self.set_up_patch("vnet_manager.operations.image.get_lxd_client")
        self.images = MagicMock()
        self.client.return_value.images = self.images
        self.images.get_by_alias.return_value = True
        self.images.exists.return_value = True

    def test_check_if_lxc_image_exists_calls_get_lxd_client(self):
        check_if_lxc_image_exists("test")
        self.client.assert_called_once_with()

    def test_check_if_lxc_image_exists_call_get_by_alias(self):
        check_if_lxc_image_exists("test")
        self.images.get_by_alias.assert_called_once_with("test")

    def test_check_if_lxc_image_exists_returns_true_if_get_by_alias_returns_true(self):
        self.images.exists.return_value = False
        self.assertTrue(check_if_lxc_image_exists("test"))

    def test_check_if_lxc_image_exists_does_not_call_exists_if_get_by_alias_succeeds(self):
        self.assertTrue(check_if_lxc_image_exists("test"))
        self.assertFalse(self.images.exists.called)

    def test_check_if_lxc_image_exists_does_not_call_exists_if_get_by_alias_fails(self):
        self.images.get_by_alias.side_effect = NotFound(response="blaap")
        check_if_lxc_image_exists("test")
        self.assertFalse(self.images.exists.called)

    def test_check_if_lxc_image_exists_returns_false_if_get_by_alias_raises_not_found(self):
        self.images.get_by_alias.side_effect = NotFound(response="blaap")
        self.assertFalse(check_if_lxc_image_exists("test"))

    def test_check_if_lxc_image_exists_calls_exists_when_not_checking_by_alias(self):
        check_if_lxc_image_exists("test", by_alias=False)
        self.images.exists.assert_called_once_with("test")
        self.assertFalse(self.images.get_by_alias.called)

    def test_check_if_lxc_image_exists_returns_true_when_exists_returns_true(self):
        self.assertTrue(check_if_lxc_image_exists("test", by_alias=False))

    def test_check_if_lxc_image_returns_false_when_exists_returns_false(self):
        self.images.exists.return_value = False
        self.assertFalse(check_if_lxc_image_exists("test", by_alias=False))


class TestCreateLXCImageFromContainer(VNetTestCase):
    def setUp(self) -> None:
        self.change_status = self.set_up_patch("vnet_manager.operations.image.change_lxc_machine_status")
        self.lxd_client = self.set_up_patch("vnet_manager.operations.image.get_lxd_client")
        self.client = MagicMock()
        self.lxd_client.return_value = self.client
        self.container = MagicMock()
        self.image = MagicMock()
        self.client.containers.get.return_value = self.container
        self.container.publish.return_value = self.image

    def test_create_lxc_image_from_container_call_change_lxc_machine_status(self):
        create_lxc_image_from_container("test")
        self.change_status.assert_called_once_with("test", status="stop")

    def test_create_lxc_image_from_container_calls_get_lxd_client(self):
        create_lxc_image_from_container("test")
        self.lxd_client.assert_called_once_with()

    def test_create_lxc_image_from_container_calls_container_get_method(self):
        create_lxc_image_from_container("test")
        self.client.containers.get.assert_called_once_with("test")

    def test_create_lxc_image_from_container_calls_publish_on_container(self):
        create_lxc_image_from_container("test")
        self.container.publish.assert_called_once_with(wait=True)

    def test_create_lxc_image_from_container_does_not_add_alias_by_default(self):
        create_lxc_image_from_container("test")
        self.assertFalse(self.image.called)
        self.assertFalse(self.image.add_alias.called)

    def test_create_lxc_image_from_container_add_alias_when_requested(self):
        create_lxc_image_from_container("test", alias="test_alias", description="test_desc")
        self.image.add_alias.assert_called_once_with("test_alias", "test_desc")


class TestDestroyLXCImage(VNetTestCase):
    def setUp(self) -> None:
        self.check_if_image_exists = self.set_up_patch("vnet_manager.operations.image.check_if_lxc_image_exists")
        self.get_lxd = self.set_up_patch("vnet_manager.operations.image.get_lxd_client")
        self.client = MagicMock()
        self.get_lxd.return_value = self.client
        self.image = MagicMock()
        self.client.images.get_by_alias.return_value = self.image
        self.client.images.get.return_value = self.image

    def test_destroy_lxc_image_checks_if_image_exists(self):
        destroy_lxc_image("test")
        self.check_if_image_exists.assert_called_once_with("test", by_alias=True)

    def test_destroy_lxc_image_check_if_image_exists_without_alias(self):
        destroy_lxc_image("test", by_alias=False)
        self.check_if_image_exists.assert_called_once_with("test", by_alias=False)

    def test_destroy_lxc_image_calls_get_lxd_client(self):
        destroy_lxc_image("test")
        self.get_lxd.assert_called_once_with()

    def test_destroy_lxc_image_calls_images_get_by_alias_by_default(self):
        destroy_lxc_image("test")
        self.client.images.get_by_alias.assert_called_once_with("test")
        self.assertFalse(self.client.images.get.called)

    def test_destroy_lxc_image_calls_images_get_when_not_by_alias(self):
        destroy_lxc_image("test", by_alias=False)
        self.client.images.get.assert_called_once_with("test")
        self.assertFalse(self.client.images.get_by_alias.called)

    def test_destroy_lxc_image_does_nothing_when_image_does_not_exist(self):
        self.check_if_image_exists.return_value = False
        destroy_lxc_image("test")
        self.assertFalse(self.get_lxd.called)
        self.assertFalse(self.image.delete.called)

    def test_destroy_lxc_image_calls_image_delete_method(self):
        destroy_lxc_image("test")
        self.image.delete.assert_called_once_with()
