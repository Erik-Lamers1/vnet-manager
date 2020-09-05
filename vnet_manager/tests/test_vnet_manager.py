from unittest.mock import patch
from io import StringIO

from vnet_manager.tests import VNetTestCase
from vnet_manager.vnet_manager import parse_args

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
