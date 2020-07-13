from unittest.mock import call
from os.path import realpath

from vnet_manager.conf import settings
from vnet_manager.tests import VNetTestCase
from vnet_manager.config.config import get_config


class TestGetConfig(VNetTestCase):
    def setUp(self) -> None:
        self.get_yaml_content = self.set_up_patch("vnet_manager.config.config.get_yaml_content")
        self.get_yaml_content.side_effect = [settings.CONFIG, settings.VALIDATED_CONFIG]
        self.config_dir = self.set_up_patch("vnet_manager.config.config.dirname")
        self.config_dir.return_value = "config_dir"
        self.maxDiff = None

    def test_get_config_calls_get_yaml_contents_with_correct_paths(self):
        calls = [call("blaap"), call(settings.CONFIG_DEFAULTS_LOCATION)]
        get_config("blaap")
        self.get_yaml_content.assert_has_calls(calls)

    def test_get_config_user_config_takes_precedence_over_defaults_config(self):
        config = get_config("blaap")
        del config["config_dir"]
        self.assertEqual(config, settings.CONFIG)

    def test_get_config_calls_dirname_function(self):
        get_config("blaap")
        self.config_dir.assert_called_once_with(realpath("blaap"))

    def test_get_config_sets_config_dir_based_on_dirname_function(self):
        config = get_config("blaap")
        self.assertEqual(config["config_dir"], self.config_dir.return_value)
