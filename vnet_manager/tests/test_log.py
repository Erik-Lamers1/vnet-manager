import logging

from vnet_manager.log import setup_console_logging, get_logging_verbosity
from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings


class TestGetLoggingVerbosity(VNetTestCase):
    def test_get_logging_verbosity_never_returns_higher_number_then_defined_verbs(self):
        self.assertEqual(get_logging_verbosity(verbose=7), logging.DEBUG)

    def test_get_logging_verbosity_never_returns_lower_number_then_defined_verbs(self):
        self.assertEqual(get_logging_verbosity(quite=8), logging.CRITICAL)

    def test_get_logging_verbosity_return_error_level_if_two_quites_passed(self):
        self.assertEqual(get_logging_verbosity(verbose=1, quite=3), logging.ERROR)


class TestLog(VNetTestCase):
    def test_setup_console_logging_sets_up_INFO_logging_by_default(self):
        setup_console_logging()
        self.assertEqual(settings.LOGGING["handlers"]["console"]["level"], logging.INFO)

    def test_setup_console_logging_sets_up_passed_logging_level(self):
        setup_console_logging(logging.DEBUG)
        self.assertEqual(settings.LOGGING["handlers"]["console"]["level"], logging.DEBUG)
