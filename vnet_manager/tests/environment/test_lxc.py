from copy import deepcopy
from unittest.mock import call

from vnet_manager.tests import VNetTestCase
from vnet_manager.environment.lxc import ensure_vnet_lxc_environment, cleanup_vnet_lxc_environment, configure_lxc_base_machine
from vnet_manager.conf import settings


class TestEnsureVNetLXCEnvironment(VNetTestCase):
    def setUp(self) -> None:
        self.config = deepcopy(settings.CONFIG)
        self.check_for_supported_os = self.set_up_patch("vnet_manager.environment.lxc.check_for_supported_os")
        self.check_for_installed_packages = self.set_up_patch("vnet_manager.environment.lxc.check_for_installed_packages")
        self.check_if_lxc_storage_pool_exists = self.set_up_patch("vnet_manager.environment.lxc.check_if_lxc_storage_pool_exists")
        self.create_lxc_storage_pool = self.set_up_patch("vnet_manager.environment.lxc.create_lxc_storage_pool")
        self.check_if_lxc_profile_exists = self.set_up_patch("vnet_manager.environment.lxc.check_if_lxc_profile_exists")
        self.create_vnet_lxc_profile = self.set_up_patch("vnet_manager.environment.lxc.create_vnet_lxc_profile")
        self.check_if_lxc_image_exists = self.set_up_patch("vnet_manager.environment.lxc.check_if_lxc_image_exists")
        self.create_lxc_base_image_container = self.set_up_patch("vnet_manager.environment.lxc.create_lxc_base_image_container")
        self.change_lxc_machine_status = self.set_up_patch("vnet_manager.environment.lxc.change_lxc_machine_status")
        self.configure_lxc_base_machine = self.set_up_patch("vnet_manager.environment.lxc.configure_lxc_base_machine")
        self.create_lxc_image_from_container = self.set_up_patch("vnet_manager.environment.lxc.create_lxc_image_from_container")
        self.destroy_lxc_machine = self.set_up_patch("vnet_manager.environment.lxc.destroy_lxc_machine")
        self.logger = self.set_up_patch("vnet_manager.environment.lxc.logger")

    def test_ensure_vnet_lxc_environment_does_nothing_if_no_lxc_machines_in_config(self):
        self.config["machines"] = {}
        ensure_vnet_lxc_environment(self.config)
        self.logger.debug.assert_called_once_with("Skipping LXC environment creation, no LXC machines in config")
        self.assertFalse(self.create_lxc_storage_pool.called)

    def test_ensure_vnet_lxc_environment_throws_runtime_error_when_running_on_unsupported_os(self):
        self.check_for_supported_os.return_value = False
        with self.assertRaises(RuntimeError):
            ensure_vnet_lxc_environment(self.config)
        self.logger.critical.assert_called_once_with("Unable to create LXC environment on your machine, OS not supported")

    def test_ensure_vnet_lxc_environment_throws_runtime_error_when_check_for_installed_packages_fails(self):
        self.check_for_installed_packages.return_value = False
        with self.assertRaises(RuntimeError):
            ensure_vnet_lxc_environment(self.config)
        self.logger.critical.assert_called_once_with(
            "Not all required host packages seem to be installed, please fix this before proceeding"
        )

    def test_ensure_vnet_lxc_environment_does_not_call_create_vnet_storage_pool_if_it_exists(self):
        self.check_if_lxc_storage_pool_exists.return_value = True
        ensure_vnet_lxc_environment(self.config)
        self.assertFalse(self.create_lxc_storage_pool.called)
        self.logger.debug.has_calls(call("VNet LXC storage pool {} found".format(settings.LXC_STORAGE_POOL_NAME)))

    def test_ensure_vnet_lxc_environment_calls_create_vnet_storage_pool_if_does_not_exist(self):
        self.check_if_lxc_storage_pool_exists.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.create_lxc_storage_pool.assert_called_once_with(name=settings.LXC_STORAGE_POOL_NAME, driver=settings.LXC_STORAGE_POOL_DRIVER)

    def test_ensure_vnet_lxc_environment_does_not_call_create_vnet_profile_if_it_exists(self):
        self.check_if_lxc_profile_exists.return_value = True
        ensure_vnet_lxc_environment(self.config)
        self.assertFalse(self.create_vnet_lxc_profile.called)
        self.logger.debug.has_calls(call("VNet profile {} found".format(settings.LXC_VNET_PROFILE)))

    def test_ensure_vnet_lxc_environment_calls_create_vnet_lxc_profile_if_it_does_not_exist(self):
        self.check_if_lxc_profile_exists.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.create_vnet_lxc_profile.assert_called_once_with(settings.LXC_VNET_PROFILE)

    def test_ensure_vnet_lxc_environment_does_not_call_base_image_creation_functions_when_it_exists(self):
        self.check_if_lxc_image_exists.return_value = True
        ensure_vnet_lxc_environment(self.config)
        self.assertFalse(self.create_lxc_base_image_container.called)
        self.assertFalse(self.change_lxc_machine_status.called)
        self.assertFalse(self.configure_lxc_base_machine.called)
        self.assertFalse(self.create_lxc_image_from_container.called)
        self.assertFalse(self.destroy_lxc_machine.called)
        self.logger.debug.has_calls(call("Base image {} found".format(settings.LXC_BASE_IMAGE_ALIAS)))

    def test_ensure_vnet_lxc_environment_calls_base_image_creation_funtions_when_it_does_not_exist(self):
        self.check_if_lxc_image_exists.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.create_lxc_base_image_container.assert_called_once_with(self.config)
        self.change_lxc_machine_status.assert_called_once_with(settings.LXC_BASE_IMAGE_MACHINE_NAME, status="start")
        self.configure_lxc_base_machine.assert_called_once_with(self.config)
        self.create_lxc_image_from_container.assert_called_once_with(
            settings.LXC_BASE_IMAGE_MACHINE_NAME, alias=settings.LXC_BASE_IMAGE_ALIAS
        )
        self.destroy_lxc_machine.assert_called_once_with(settings.LXC_BASE_IMAGE_MACHINE_NAME, wait=False)


class TestCleanupVNetLXCEnvironment(VNetTestCase):
    def setUp(self) -> None:
        self.confirm = self.set_up_patch("vnet_manager.environment.lxc.request_confirmation")
        self.delete_vnet_lxc_profile = self.set_up_patch("vnet_manager.environment.lxc.delete_vnet_lxc_profile")
        self.delete_lxc_storage_pool = self.set_up_patch("vnet_manager.environment.lxc.delete_lxc_storage_pool")

    def test_cleanup_vnet_lxc_environment_calls_correct_functions(self):
        cleanup_vnet_lxc_environment()
        self.confirm.assert_called_once_with(message="Cleanup will delete the VNet LXC configurations, such as profile and storage pools")
        self.delete_vnet_lxc_profile.assert_called_once_with(settings.LXC_VNET_PROFILE)
        self.delete_lxc_storage_pool.assert_called_once_with(settings.LXC_STORAGE_POOL_NAME)
