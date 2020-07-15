from io import StringIO
from unittest.mock import patch

from vnet_manager.tests import VNetTestCase
from vnet_manager.actions.help import display_help_for_action
from vnet_manager.conf import settings


class TestDisplayHelpForAction(VNetTestCase):
    def setUp(self) -> None:
        self.logger = self.set_up_patch("vnet_manager.actions.help.logger")

    def test_display_help_for_action_does_not_print_anything_if_unknown_action(self):
        display_help_for_action("banana")
        self.logger.warning.called_once_with("No help text available for action banana")
        self.assertFalse(self.logger.debug.called)

    @patch("sys.stdout", new_callable=StringIO)
    def test_display_help_for_action_prints_mapped_help_text(self, mock):
        display_help_for_action("start")
        self.assertEqual(mock.getvalue().strip(), settings.HELP_TEXT_ACTION_MAPPING["start"].strip())
