import logging
import logging.config

from vnet_manager.conf import settings


def setup_console_logging(verbosity=logging.INFO):
    """
    :param int verbosity: Verbosity level logging.<verbosity>
    """
    settings.LOGGING["handlers"]["console"]["level"] = verbosity
    settings.LOGGING["handlers"]["syslog"]["level"] = verbosity
    logging.config.dictConfig(settings.LOGGING)
