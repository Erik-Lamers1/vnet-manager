from vnet_manager.tests import VNetTestCase
from vnet_manager.environment.host import check_for_supported_os


class TestCheckForSupportedOS(VNetTestCase):
    def setUp(self) -> None:
        self.codename = self.set_up_patch("vnet_manager.environment.host.codename")
        self.codename.return_value = "bionic"

    def test_check_for_supported_os_returns_true_if_os_supported(self):
        self.assertTrue(check_for_supported_os("lxc"))

    def test_check_for_supported_os_returns_false_if_os_not_supported(self):
        self.codename.return_value = "Hannah Montana Linux"
        self.assertFalse(check_for_supported_os("lxc"))
