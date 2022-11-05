from unittest.mock import Mock
from os import environ, EX_NOPERM
from logging import INFO, DEBUG

from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings
from vnet_manager.vnet_manager import main

default_args = ["create", "config"]


class TestVNetManagerMain(VNetTestCase):
    def setUp(self) -> None:
        self.setup_console_logging = self.set_up_patch("vnet_manager.vnet_manager.setup_console_logging")
        self.check_for_root_user = self.set_up_patch("vnet_manager.vnet_manager.check_for_root_user")
        self.manager = Mock()
        self.action_manager = self.set_up_patch("vnet_manager.vnet_manager.ActionManager")
        self.action_manager.return_value = self.manager
        self.environ = dict(environ)

    def tearDown(self) -> None:
        environ.clear()
        environ.update(self.environ)

    def test_main_sets_vnet_force_env_variable_to_false_by_default(self):
        main(default_args)
        self.assertEqual(environ[settings.VNET_FORCE_ENV_VAR], "false")

    def test_main_sets_vnet_force_env_variable_to_true_when_yes_passed(self):
        main(default_args + ["--yes"])
        self.assertEqual(environ[settings.VNET_FORCE_ENV_VAR], "true")

    def test_main_calls_setup_console_logging(self):
        main(default_args)
        self.setup_console_logging.assert_called_once_with(verbosity=INFO)

    def test_main_call_setup_console_logging_with_verbose(self):
        main(default_args + ["--verbose"])
        self.setup_console_logging.assert_called_once_with(verbosity=DEBUG)

    def test_main_calls_check_for_root_user(self):
        main(default_args)
        self.check_for_root_user.assert_called_once_with()

    def test_main_returns_non_zero_exit_code_when_no_root_user_detected(self):
        self.check_for_root_user.return_value = False
        ret = main(default_args)
        self.assertEqual(ret, EX_NOPERM)
        self.assertFalse(self.action_manager.called)

    def test_main_calls_action_manager(self):
        main(default_args)
        self.action_manager.assert_called_once_with(
            base_image=False,
            config_path="config",
            no_hosts=False,
            sniffer=False,
            purge=False,
            provider=None,
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )

    def test_main_calls_action_manager_with_base_image(self):
        main(["destroy", "--base-image"])
        self.action_manager.assert_called_once_with(
            base_image=True,
            config_path=None,
            no_hosts=False,
            sniffer=False,
            purge=False,
            provider=None,
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )

    def test_main_calls_action_manager_with_no_hosts(self):
        main(["create", "config", "--no-hosts"])
        self.action_manager.assert_called_once_with(
            base_image=False,
            config_path="config",
            no_hosts=True,
            sniffer=False,
            purge=False,
            provider=None,
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )

    def test_main_calls_action_manager_with_sniffer(self):
        main(["start", "config", "--sniffer"])
        self.action_manager.assert_called_once_with(
            base_image=False,
            config_path="config",
            no_hosts=False,
            sniffer=True,
            purge=False,
            provider=None,
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )

    def test_main_calls_action_manager_with_default_provider_on_connect(self):
        main(["connect", "machine1"])
        self.action_manager.assert_called_once_with(
            base_image=False,
            config_path="machine1",
            no_hosts=False,
            sniffer=False,
            purge=False,
            provider="lxc",
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )

    def test_main_calls_action_manager_with_provider(self):
        main(["connect", "machine1", "--provider", "test"])
        self.action_manager.assert_called_once_with(
            base_image=False,
            config_path="machine1",
            no_hosts=False,
            sniffer=False,
            purge=False,
            provider="test",
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )

    def test_main_sets_manager_machine_attribute(self):
        main(default_args + ["--machines", "test1", "test2"])
        self.assertEqual(self.manager.machines, ["test1", "test2"])

    def test_main_returns_action_manager_execute_return_value(self):
        self.manager.execute.return_value = 42
        ret = main(default_args)
        self.assertEqual(ret, 42)

    def test_main_executes_status_action_with_show_call(self):
        main(["status", "config"])
        self.manager.execute.assert_called_once_with("show")

    def test_main_calls_vnet_manager_with_purge(self):
        main(["destroy", "--purge"])
        self.action_manager.assert_called_once_with(
            base_image=False,
            config_path=None,
            no_hosts=False,
            sniffer=False,
            purge=True,
            provider=None,
            pcap_dir=settings.VNET_SNIFFER_PCAP_DIR,
        )
        self.manager.execute.assert_called_once_with("destroy")

    def test_main_calls_manager_with_version(self):
        main(["version"])
        self.manager.execute.assert_called_once_with("version")
