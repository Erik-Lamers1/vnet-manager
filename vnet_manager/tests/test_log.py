import logging

from vnet_manager.log import setup_console_logging
from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings


class TestLog(VNetTestCase):
    def test_setup_console_logging_sets_up_INFO_logging_by_default(self):
        setup_console_logging()
        self.assertEqual(settings.LOGGING["handlers"]["console"]["level"], logging.INFO)

    def test_setup_console_logging_sets_up_passed_logging_level(self):
        setup_console_logging(logging.DEBUG)
        self.assertEqual(settings.LOGGING["handlers"]["console"]["level"], logging.DEBUG)
