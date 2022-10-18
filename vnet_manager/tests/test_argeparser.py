from argparse import Namespace
from io import StringIO
from unittest.mock import patch

from vnet_manager.argeparser import parse_vnet_args
from vnet_manager.tests import VNetTestCase


default_args = ["create", "config_test"]


class TestParseArgs(VNetTestCase):
    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_config_required_action_without_config_is_passed(self, stderr):
        with self.assertRaises(SystemExit):
            parse_vnet_args(["create"])
        self.assertTrue(stderr.getvalue().strip().endswith(""))

    def test_parse_args_accepts_no_hosts_on_create(self):
        self.assertIsInstance(parse_vnet_args(["create", "config", "--no-hosts"]), Namespace)

    def test_parse_args_accepts_machines_on_create(self):
        self.assertIsInstance(parse_vnet_args(["create", "config", "--machines", "machine1"]), Namespace)

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_sniffer_is_passed_without_start_action(self, stderr):
        with self.assertRaises(SystemExit):
            parse_vnet_args(["list", "config", "--sniffer"])
        self.assertTrue(stderr.getvalue().strip().endswith("unrecognized arguments: --sniffer"))

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_base_image_passed_without_destroy_action(self, stderr):
        with self.assertRaises(SystemExit):
            parse_vnet_args(["list", "config", "--base-image"])
        self.assertTrue(stderr.getvalue().strip().endswith("unrecognized arguments: --base-image"))

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_no_hosts_passed_without_create_action(self, stderr):
        with self.assertRaises(SystemExit):
            parse_vnet_args(["list", "config", "--no-hosts"])
        self.assertTrue(stderr.getvalue().strip().endswith("unrecognized arguments: --no-hosts"))

    def test_parse_args_accepts_sniffer_on_start(self):
        self.assertIsInstance(parse_vnet_args(["start", "config", "--sniffer"]), Namespace)

    def test_parse_args_accepts_machines_on_start(self):
        self.assertIsInstance(parse_vnet_args(["start", "config", "--machines", "machine1"]), Namespace)

    def test_parse_args_accepts_pcap_dir_on_start(self):
        self.assertIsInstance(parse_vnet_args(["start", "config", "-pd", "/tmp"]), Namespace)

    def test_parse_args_accepts_machines_on_stop(self):
        self.assertIsInstance(parse_vnet_args(["stop", "config", "--machines", "machine1"]), Namespace)

    def test_parse_args_accepts_provider_on_connect(self):
        self.assertIsInstance(parse_vnet_args(["connect", "machine1", "--provider", "test"]), Namespace)

    @patch("sys.stderr", new_callable=StringIO)
    def test_parse_args_exists_when_no_machine_name_passed_to_connect(self, stderr):
        with self.assertRaises(SystemExit):
            parse_vnet_args(["connect"])
        self.assertTrue(stderr.getvalue().strip().endswith("the following arguments are required: machine"))

    def test_parse_args_accepts_verbose_after_action(self):
        self.assertIsInstance(parse_vnet_args(["connect", "machine1", "--verbose"]), Namespace)

    def test_parse_args_accepts_quite_after_action(self):
        self.assertIsInstance(parse_vnet_args(["bash-completion", "--quite"]), Namespace)

    def test_parse_args_accepts_yes_after_action(self):
        self.assertIsInstance(parse_vnet_args(["create", "connect", "--yes"]), Namespace)
