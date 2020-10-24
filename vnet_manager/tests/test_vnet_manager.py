from unittest.mock import patch, Mock
from io import StringIO
from os import environ, EX_NOPERM
from logging import INFO, DEBUG

from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings
from vnet_manager.vnet_manager import parse_args, main

default_args = ["list", "config"]


class TestParseArgs(VNetTestCase):
    def test_parse_args_produces_known_args(self):
        known_args = ("action", "config", "machines", "yes", "verbose", "sniffer", "base_image", "no_hosts")
        args = parse_args(default_args)
        for arg in known_args:
            self.assertTrue(hasattr(args, arg), msg="Argument {} not found in parse_args return value".format(arg))

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_config_required_action_without_config_is_passed(self, stderr):
        with self.assertRaises(SystemExit):
            parse_args(["create"])
        self.assertTrue(stderr.getvalue().strip().endswith("This action requires a config file to be passed"))

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_sniffer_is_passed_without_start_action(self, stderr):
        with self.assertRaises(SystemExit):
            parse_args(["list", "config", "--sniffer"])
        self.assertTrue(stderr.getvalue().strip().endswith("The sniffer option only makes sense with the 'start' action"))

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_base_image_passed_without_destroy_action(self, stderr):
        with self.assertRaises(SystemExit):
            parse_args(["list", "config", "--base-image"])
        self.assertTrue(stderr.getvalue().strip().endswith("The base_image option only makes sense with the 'destroy' action"))

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_no_hosts_passed_without_create_action(self, stderr):
        with self.assertRaises(SystemExit):
            parse_args(["list", "config", "--no-hosts"])
        self.assertTrue(stderr.getvalue().strip().endswith("The no_hosts option only makes sense with the 'create' action"))


class TestVNetManagerMain(VNetTestCase):
    def setUp(self) -> None:
        self.setup_console_logging = self.set_up_patch("vnet_manager.vnet_manager.setup_console_logging")
        self.check_for_root_user = self.set_up_patch("vnet_manager.vnet_manager.check_for_root_user")
        self.manager = Mock()
        self.action_manager = self.set_up_patch("vnet_manager.vnet_manager.ActionManager")
        self.action_manager.return_value = self.manager

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
        self.action_manager.assert_called_once_with(base_image=False, config_path="config", no_hosts=False, sniffer=False)

    def test_main_calls_action_manager_with_base_image(self):
        main(["destroy", "config", "--base-image"])
        self.action_manager.assert_called_once_with(base_image=True, config_path="config", no_hosts=False, sniffer=False)

    def test_main_calls_action_manager_with_no_hosts(self):
        main(["create", "config", "--no-hosts"])
        self.action_manager.assert_called_once_with(base_image=False, config_path="config", no_hosts=True, sniffer=False)

    def test_main_calls_action_manager_with_sniffer(self):
        main(["start", "config", "--sniffer"])
        self.action_manager.assert_called_once_with(base_image=False, config_path="config", no_hosts=False, sniffer=True)

    def test_main_sets_manager_machine_attribute(self):
        main(default_args + ["--machines", "test1", "test2"])
        self.assertEqual(self.manager.machines, ["test1", "test2"])

    def test_main_returns_action_manager_execute_return_value(self):
        self.manager.execute.return_value = 42
        ret = main(default_args)
        self.assertEqual(ret, 42)
