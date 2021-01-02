from os import environ

from vnet_manager.conf import settings
from vnet_manager.tests import VNetTestCase
from vnet_manager.utils.user import check_for_root_user, request_confirmation, generate_bash_completion_script


def my_func():
    pass


class TestCheckForRootUser(VNetTestCase):
    def setUp(self) -> None:
        self.geteuid = self.set_up_patch("vnet_manager.utils.user.geteuid")
        self.geteuid.return_value = 0

    def test_check_for_root_user_calls_geteuid(self):
        check_for_root_user()
        self.geteuid.assert_called_once_with()

    def test_check_for_root_user_returns_true_if_geteuid_is_zero(self):
        self.assertTrue(check_for_root_user())

    def test_check_for_root_user_return_false_if_geteuid_is_not_zero(self):
        self.geteuid.return_value = 1
        self.assertFalse(check_for_root_user())


class TestRequestConfirmation(VNetTestCase):
    def setUp(self) -> None:
        self.input = self.set_up_patch("builtins.input")
        self.input.return_value = "yes"
        self.environ = dict(environ)

    def tearDown(self) -> None:
        environ.clear()
        environ.update(self.environ)

    def test_request_confirmation_calls_input(self):
        request_confirmation(prompt="test")
        self.input.assert_called_once_with("test")

    def test_request_confirmation_calls_input_multiple_times(self):
        self.input.side_effect = ["blaap", "bloep", "yes"]
        request_confirmation(prompt="test")
        self.assertEqual(self.input.call_count, 3)

    def test_request_confirmation_calls_sys_exit_by_default_when_user_answers_no(self):
        self.input.return_value = "no"
        with self.assertRaises(SystemExit) as e:
            request_confirmation(prompt="test")
        self.assertEqual(e.exception.code, 1)

    def test_request_confirmation_calls_custom_function_when_passed(self):
        self.input.return_value = "no"
        self.my_func = self.set_up_patch("vnet_manager.tests.utils.test_user.my_func")
        request_confirmation(prompt="test", func=my_func, args=["arg"], kwargs={"kwarg": 1})
        self.my_func.assert_called_once_with("arg", kwarg=1)

    def test_request_confirmation_does_not_call_input_when_force_env_var_set(self):
        environ[settings.VNET_FORCE_ENV_VAR] = "true"
        request_confirmation(prompt="test")
        self.assertFalse(self.input.called)


class TestGenerateBashCompletionScript(VNetTestCase):
    def test_generate_bash_completion_script_returns_string(self):
        self.assertIsInstance(generate_bash_completion_script(), str)

    def test_generate_bash_completion_script_starts_with_shebang(self):
        self.assertTrue(generate_bash_completion_script().startswith("#!/usr/bin/env bash"))
