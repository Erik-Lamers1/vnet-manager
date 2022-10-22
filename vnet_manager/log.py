import logging
import logging.config

from vnet_manager.conf import settings


def get_logging_verbosity(verbose: int = 0, quite: int = 0, default_verbosity: int = settings.LOGGING_DEFAULT_VERBOSITY) -> int:
    """
    Get the logging verbosity based upon any passed verbosity arguments
    :param verbose: int: The amount of verbosity to add
    :param quite: int: The inverse amount of verbosity to add
    :param default_verbosity: int, the initial verbosity to manipulate
    :return: int: The logging verbosity setting
    """
    logging_verbs = {0: logging.CRITICAL, 1: logging.ERROR, 2: logging.WARNING, 3: logging.INFO, 4: logging.DEBUG}
    # Compare the amount of verbosity args against the default verbosity
    mod = default_verbosity + verbose - quite
    # Return the appropriate logging level (must be within the defined logging levels)
    return logging_verbs[max(min(len(logging_verbs) - 1, mod), 0)]


def setup_console_logging(verbosity: int = logging.INFO) -> None:
    """
    :param int verbosity: Verbosity level logging.<verbosity>
    """
    settings.LOGGING["handlers"]["console"]["level"] = verbosity
    settings.LOGGING["handlers"]["syslog"]["level"] = verbosity
    logging.config.dictConfig(settings.LOGGING)
