import logging
from argparse import ArgumentParser

from vnet_manager.log import setup_console_logging, get_logging_verbosity
from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings


def my_test_args(args):
    parser = ArgumentParser()
    parser.add_argument("-q", "--quite", action="count", default=0)
    parser.add_argument("-v", "--verbose", action="count", default=0)
    return parser.parse_args(args=args)


class TestGetLoggingVerbosity(VNetTestCase):
    def test_get_logging_verbosity_never_returns_higher_number_then_defined_verbs(self):
        args = my_test_args(["-vvvvvvvvvvv", "--verbose", "-v"])
        self.assertEqual(get_logging_verbosity(args), logging.DEBUG)

    def test_get_logging_verbosity_never_returns_lower_number_then_defined_verbs(self):
        args = my_test_args(["-qqqqqqqqqqq", "--quite", "-q"])
        self.assertEqual(get_logging_verbosity(args), logging.CRITICAL)

    def test_get_logging_verbosity_return_error_level_if_two_quites_passed(self):
        args = my_test_args(["--quite", "-q"])
        self.assertEqual(get_logging_verbosity(args), logging.ERROR)


class TestLog(VNetTestCase):
    def test_setup_console_logging_sets_up_INFO_logging_by_default(self):
        setup_console_logging()
        self.assertEqual(settings.LOGGING["handlers"]["console"]["level"], logging.INFO)

    def test_setup_console_logging_sets_up_passed_logging_level(self):
        setup_console_logging(logging.DEBUG)
        self.assertEqual(settings.LOGGING["handlers"]["console"]["level"], logging.DEBUG)
