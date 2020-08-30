from unittest.mock import MagicMock

from vnet_manager.tests import VNetTestCase
from vnet_manager.environment.host import check_for_installed_packages, check_for_supported_os
from vnet_manager.conf import settings


class TestCheckForSupportedOS(VNetTestCase):
    def setUp(self) -> None:
        self.codename = self.set_up_patch("vnet_manager.environment.host.codename")
        self.codename.return_value = "bionic"
        self.config = settings.CONFIG

    def test_check_for_supported_os_returns_true_if_os_supported(self):
        self.assertTrue(check_for_supported_os(self.config, "lxc"))

    def test_check_for_supported_os_returns_false_if_os_not_supported(self):
        self.codename.return_value = "Hannah Montana Linux"
        self.assertFalse(check_for_supported_os(self.config, "lxc"))


class TestCheckForInstalledPackages(VNetTestCase):
    def setUp(self) -> None:
        self.cache = self.set_up_patch("vnet_manager.environment.host.Cache", themock=MagicMock())
        self.logger = self.set_up_patch("vnet_manager.environment.host.logger")
        self.config = settings.CONFIG

    def test_check_for_installed_packages_calls_apt_cache(self):
        check_for_installed_packages(self.config, "lxc")
        self.cache.assert_called_once_with()

    def test_check_for_installed_packages_returns_true_if_all_packages_installed(self):
        self.assertTrue(check_for_installed_packages(self.config, "lxc"))

    def test_check_for_installed_packages_returns_false_if_not_all_packages_installed(self):
        self.cache.return_value[self.config["providers"]["lxc"]["required_host_packages"][0]].is_installed = False
        self.assertFalse(check_for_installed_packages(self.config, "lxc"))
