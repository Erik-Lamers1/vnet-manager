from unittest.mock import patch
from io import StringIO
from os import environ
from logging import INFO, DEBUG

from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings
from vnet_manager.vnet_manager import parse_args, main

default_args = ["list", "config"]


class TestParseArgs(VNetTestCase):
    def test_parse_args_produces_known_args(self):
        known_args = ("action", "config", "machines", "yes", "verbose", "sniffer", "base_image")
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


class TestVNetManagerMain(VNetTestCase):
    def setUp(self) -> None:
        self.setup_console_logging = self.set_up_patch("vnet_manager.vnet_manager.setup_console_logging")
        self.check_for_root_user = self.set_up_patch("vnet_manager.vnet_manager.check_for_root_user")
        self.action_manager = self.set_up_patch("vnet_manager.vnet_manager.ActionManager")

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
