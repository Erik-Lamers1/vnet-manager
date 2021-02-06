from logging import makeLogRecord, Formatter, WARNING

from vnet_manager.tests import VNetTestCase
from vnet_manager.utils.logging.formatters import ConsoleFormatter


class TestConsoleFormatter(VNetTestCase):
    def setUp(self) -> None:
        self.record = makeLogRecord(
            {
                "name": "salty.sub",
                "levelno": WARNING,
                "levelname": "WARNING",
                "msg": "mocked log",
            }
        )
        self.formatter = ConsoleFormatter()
        self.fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def test_console_formatter_extends_formatter(self):
        self.assertIsInstance(self.formatter, Formatter)

    def test_console_formatter_formats_when_not_colored_with_default_fmt(self):
        formatter = ConsoleFormatter(colored=False)
        self.assertEqual(formatter.format(self.record), Formatter().format(self.record))

    def test_console_formatter_formats_when_not_colored_with_custom_fmt(self):
        formatter = ConsoleFormatter(self.fmt, colored=False)
        self.assertEqual(formatter.format(self.record), Formatter(self.fmt).format(self.record))

    def test_console_formatter_formats_when_colored_with_default_fmt(self):
        colorless_msg = Formatter().format(self.record)
        colored_msg = ConsoleFormatter(colored=True).format(self.record)

        self.assertNotEqual(colorless_msg, colored_msg)
        for word in colorless_msg.split():
            self.assertIn(word, colored_msg)

    def test_console_formatter_formats_when_colored_with_custom_fmt(self):
        colorless_msg = Formatter(self.fmt).format(self.record)
        colored_msg = ConsoleFormatter(self.fmt, colored=True).format(self.record)

        self.assertNotEqual(colorless_msg, colored_msg)
        for word in colorless_msg.split():
            self.assertIn(word, colored_msg)

    def test_console_formatter_accepts_functions_to_detect_colored(self):
        is_colored_calls = []

        def is_colored():
            is_colored_calls.append(True)
            return True

        colorless_msg = Formatter().format(self.record)
        colored_msg = ConsoleFormatter(colored=is_colored).format(self.record)

        self.assertNotEqual(colorless_msg, colored_msg)
        for word in colorless_msg.split():
            self.assertIn(word, colored_msg)

        self.assertEqual(is_colored_calls, [True])

    def test_console_formatter_wont_color_if_colored_func_returns_false(self):
        formatter = ConsoleFormatter(colored=lambda: False)
        self.assertEqual(formatter.format(self.record), Formatter().format(self.record))

    def test_console_formatter_does_not_accept_args_other_than_bool_or_callable(self):
        with self.assertRaises(TypeError):
            ConsoleFormatter(colored="i am not bool nor function")
