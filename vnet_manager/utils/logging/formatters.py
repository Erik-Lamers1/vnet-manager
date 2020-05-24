from copy import deepcopy
from logging import Formatter, INFO, DEBUG, WARNING, ERROR, CRITICAL
import warnings

try:
    import colorama
except ImportError:
    colorama = None

if colorama:
    default_palette = {
        "asctime": {"*": [colorama.Fore.BLACK, colorama.Style.BRIGHT],},
        "level": {
            DEBUG: [colorama.Fore.WHITE, colorama.Style.DIM],
            WARNING: [colorama.Fore.YELLOW],
            ERROR: [colorama.Fore.RED],
            CRITICAL: [colorama.Fore.RED, colorama.Style.BRIGHT],
        },
        "msg": {
            DEBUG: [colorama.Fore.WHITE, colorama.Style.DIM],
            WARNING: [colorama.Style.BRIGHT],
            ERROR: [colorama.Fore.RED],
            CRITICAL: [colorama.Fore.RED, colorama.Style.BRIGHT],
        },
    }
    _RESET = colorama.Style.RESET_ALL
else:
    default_palette = {"asctime": {}, "level": {}, "msg": {}}
    _RESET = ""


class ConsoleFormatter(Formatter):
    """
    ConsoleFormatter is a log formatter to color log attributes for console printing

    :param str fmt: format string
    :param str datefmt: format string for log date time
    :param bool|callable colored: if should add ANSI colors to logs. If not a bool, it's called as a function
    and the return value is treated as bool
    See logging.Formatter
    """

    def __init__(self, fmt=None, datefmt=None, colored=True):
        Formatter.__init__(self, fmt, datefmt)
        self._colored = bool(colored()) if colored and not isinstance(colored, bool) else colored
        if self._colored and not colorama:
            warnings.warn("can't format colored log message. dependency package 'colorama' is not installed")
            self._colored = False
        self._palette = default_palette if self._colored else {"asctime": {}, "level": {}, "msg": {}}

    @property
    def colored(self):
        return self._colored

    def format(self, record):
        """
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string uses the
        time (as determined by a call to usesTime(), formatTime() is
        called to format the event time. If there is exception information,
        it is formatted using formatException() and appended to the message.

        See logging.Format.format
        """
        if self._colored:
            return self._colored_format(record)
        return Formatter.format(self, record)

    def _colored_format(self, record):
        """
        Format the specified record as text colored using ANSI escape sequences

        See format
        """
        record = deepcopy(record)  # avoid mutating the record itself
        level = getattr(record, "levelno", INFO)

        level_palette = self._palette["level"]
        level_styles = level_palette[level] if level in level_palette else level_palette.get("*", [])
        if level_styles:
            record.levelname = r"".join(level_styles) + str(record.levelname) + _RESET

        msg_palette = self._palette["msg"]
        msg_styles = msg_palette[level] if level in msg_palette else msg_palette.get("*", [])
        if msg_styles:
            record.msg = r"".join(msg_styles) + str(record.msg) + _RESET

        return Formatter.format(self, record)

    def formatTime(self, record, datefmt=None):
        """
        Return the creation time of the specified LogRecord as formatted text.

        This method should be called from format()

        See logging.Formatter.formatTime
        """
        formatted_time = Formatter.formatTime(self, record, datefmt)
        if self._colored:
            level = getattr(record, "levelno", INFO)
            asctime_palette = self._palette["asctime"]
            asctime_styles = asctime_palette[level] if level in asctime_palette else asctime_palette.get("*", [])
            if asctime_styles:
                return r"".join(asctime_styles) + formatted_time + _RESET
        return formatted_time
