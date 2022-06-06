from copy import deepcopy
import shlex
from unittest.mock import call, MagicMock

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
        self.confirm = self.set_up_patch("vnet_manager.environment.lxc.request_confirmation")

    def test_ensure_vnet_lxc_environment_does_nothing_if_no_lxc_machines_in_config(self):
        self.config["machines"] = {}
        ensure_vnet_lxc_environment(self.config)
        self.logger.debug.assert_called_once_with("Skipping LXC environment creation, no LXC machines in config")
        self.assertFalse(self.create_lxc_storage_pool.called)

    def test_ensure_vnet_lxc_environment_displays_warning_when_os_not_supported(self):
        self.check_for_supported_os.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.confirm.assert_called_once_with(
            message="Unsupported OS detected, LXC is tested on the following systems; bionic, focal", prompt="Continue anyway? (y/n) "
        )

    def test_ensure_vnet_lxc_environment_displays_warning_when_missing_apt_packages_detected(self):
        self.check_for_installed_packages.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.confirm.assert_called_once_with(
            message="Missing APT packages detected, this might break operations", prompt="Continue anyway? (y/n) "
        )

    def test_ensure_vnet_lxc_environment_does_not_call_create_vnet_storage_pool_if_it_exists(self):
        self.check_if_lxc_storage_pool_exists.return_value = True
        ensure_vnet_lxc_environment(self.config)
        self.assertFalse(self.create_lxc_storage_pool.called)
        self.logger.debug.has_calls(call(f"VNet LXC storage pool {settings.LXC_STORAGE_POOL_NAME} found"))

    def test_ensure_vnet_lxc_environment_calls_create_vnet_storage_pool_if_does_not_exist(self):
        self.check_if_lxc_storage_pool_exists.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.create_lxc_storage_pool.assert_called_once_with(name=settings.LXC_STORAGE_POOL_NAME, driver=settings.LXC_STORAGE_POOL_DRIVER)

    def test_ensure_vnet_lxc_environment_does_not_call_create_vnet_profile_if_it_exists(self):
        self.check_if_lxc_profile_exists.return_value = True
        ensure_vnet_lxc_environment(self.config)
        self.assertFalse(self.create_vnet_lxc_profile.called)
        self.logger.debug.has_calls(call(f"VNet profile {settings.LXC_VNET_PROFILE} found"))

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
        self.logger.debug.has_calls(call(f"Base image {settings.LXC_BASE_IMAGE_ALIAS} found"))

    def test_ensure_vnet_lxc_environment_calls_base_image_creation_funtions_when_it_does_not_exist(self):
        self.check_if_lxc_image_exists.return_value = False
        ensure_vnet_lxc_environment(self.config)
        self.create_lxc_base_image_container.assert_called_once_with()
        self.change_lxc_machine_status.assert_called_once_with(settings.LXC_BASE_IMAGE_MACHINE_NAME, status="start")
        self.configure_lxc_base_machine.assert_called_once_with()
        self.create_lxc_image_from_container.assert_called_once_with(
            settings.LXC_BASE_IMAGE_MACHINE_NAME, alias=settings.LXC_BASE_IMAGE_ALIAS
        )
        self.destroy_lxc_machine.assert_called_once_with(settings.LXC_BASE_IMAGE_MACHINE_NAME, wait=False)


class TestCleanupVNetLXCEnvironment(VNetTestCase):
    def setUp(self) -> None:
        self.confirm = self.set_up_patch("vnet_manager.environment.lxc.request_confirmation")
        self.delete_vnet_lxc_profile = self.set_up_patch("vnet_manager.environment.lxc.delete_vnet_lxc_profile")
        self.delete_lxc_storage_pool = self.set_up_patch("vnet_manager.environment.lxc.delete_lxc_storage_pool")
        self.destroy_image = self.set_up_patch("vnet_manager.environment.lxc.destroy_lxc_image")

    def test_cleanup_vnet_lxc_environment_calls_correct_functions(self):
        cleanup_vnet_lxc_environment()
        self.confirm.assert_called_once_with(
            message="Cleanup will delete the VNet LXC configurations, such as base_image, profile and storage pools"
        )
        self.delete_vnet_lxc_profile.assert_called_once_with(settings.LXC_VNET_PROFILE)
        self.delete_lxc_storage_pool.assert_called_once_with(settings.LXC_STORAGE_POOL_NAME)
        self.destroy_image.assert_called_once_with(settings.LXC_BASE_IMAGE_ALIAS, by_alias=True, wait=True)


class TestConfigureLXCBaseMachine(VNetTestCase):
    def setUp(self) -> None:
        self.get_lxd_client = self.set_up_patch("vnet_manager.environment.lxc.get_lxd_client")
        self.client = MagicMock()
        self.machine = MagicMock()
        self.get_lxd_client.return_value = self.client
        self.client.containers.get.return_value = self.machine
        self.machine.execute.return_value = [0]
        self.sleep = self.set_up_patch("vnet_manager.environment.lxc.sleep")

    def test_configure_lxc_base_machine_check_for_dns(self):
        configure_lxc_base_machine()
        self.machine.execute.assert_has_calls([call(shlex.split("host -t A google.com"))])

    def test_configure_lxc_base_machine_does_not_continue_if_no_dns_connectivity(self):
        self.machine.execute.return_value = [1]
        with self.assertRaises(RuntimeError):
            configure_lxc_base_machine()
        self.assertTrue(self.sleep.called)

    def test_configure_lxc_base_machine_stops_base_if_no_dns_connectivity(self):
        self.machine.execute.return_value = [1]
        with self.assertRaises(RuntimeError):
            configure_lxc_base_machine()
        self.machine.stop.assert_called_once_with()

    def test_configure_lxc_base_machine_calls_correct_configure_cmds(self):
        calls = [
            call(shlex.split("bash -c 'curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add'")),
            call(
                shlex.split(
                    "bash -c 'echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) {} | "
                    "tee -a /etc/apt/sources.list.d/frr.list'".format(settings.FRR_RELEASE)
                )
            ),
            call(shlex.split("apt-get update")),
            call(
                shlex.split("apt-get upgrade -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'"),
                environment={"DEBIAN_FRONTEND": "noninteractive"},
            ),
            call(
                shlex.split(
                    "apt-get install -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold' {}".format(
                        " ".join(settings["PROVIDERS"]["lxc"]["guest_packages"])
                    )
                ),
                environment={"DEBIAN_FRONTEND": "noninteractive"},
            ),
            call(shlex.split("systemctl disable radvd")),
            call(shlex.split("bash -c 'echo network: {config: disabled} > /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg'")),
            call(shlex.split("bash -c 'export VTYSH_PAGER=more >> ~/.bashrc'")),
            call(
                shlex.split(
                    'bash -c \'echo -e "#!/bin/bash\nchown -R frr:frr /etc/frr\nsystemctl restart frr" > /etc/rc.local; chmod +x '
                    "/etc/rc.local' "
                )
            ),
        ]
        configure_lxc_base_machine()
        self.machine.execute.assert_has_calls(calls)

    def test_configure_lxc_base_machine_call_machine_stop_(self):
        configure_lxc_base_machine()
        self.machine.stop.assert_called_once_with(wait=True)
