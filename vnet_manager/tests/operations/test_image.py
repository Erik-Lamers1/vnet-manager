from unittest.mock import MagicMock
from pylxd.exceptions import NotFound

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.image import check_if_lxc_image_exists


class TestCheckIfLXCImageExists(VNetTestCase):
    def setUp(self) -> None:
        self.client = self.set_up_patch("vnet_manager.operations.image.get_lxd_client")
        self.images = MagicMock()
        self.client.return_value.images = self.images
        self.images.get_by_alias.return_value = True
        self.images.exists.return_value = True

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
