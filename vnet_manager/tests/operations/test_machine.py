from unittest.mock import Mock, MagicMock, call
from pylxd.exceptions import NotFound

from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings
from vnet_manager.operations.machine import (
    show_status,
    check_if_lxc_machine_exists,
    get_lxc_machine_status,
    wait_for_lxc_machine_status,
    change_machine_status,
    change_lxc_machine_status,
    create_machines,
)


class TestShowStatus(VNetTestCase):
    def setUp(self) -> None:
        self.tabulate = self.set_up_patch("vnet_manager.operations.machine.tabulate")
        self.get_lxc_machine_status = self.set_up_patch("vnet_manager.operations.machine.get_lxc_machine_status")
        self.get_lxc_machine_status.return_value = ["router", "up", "LXC"]
        self.config = settings.CONFIG
        # Only 1 machine for less output
        self.config["machines"].pop("router101", None)
        self.config["machines"].pop("router102", None)

    def test_show_status_call_get_lxc_machine_status(self):
        show_status(self.config)
        self.get_lxc_machine_status.assert_called_once_with("router100")

    def test_show_status_makes_correct_tabulate_call(self):
        show_status(self.config)
        self.tabulate.assert_called_once_with(
            [self.get_lxc_machine_status.return_value], headers=["Name", "Status", "Provider"], tablefmt="pretty"
        )


class TestCheckIfLXCMachineExists(VNetTestCase):
    def setUp(self) -> None:
        self.machine = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.machine.get_lxd_client")
        self.lxd_client.return_value = self.machine

    def test_check_if_lxc_machine_exists_calls_exists_method(self):
        check_if_lxc_machine_exists("test")
        self.machine.containers.exists.assert_called_once_with("test")

    def test_check_if_lxc_machine_exists_returns_value_of_exists_method(self):
        self.machine.containers.exists.return_value = False
        self.assertFalse(check_if_lxc_machine_exists("test"))


class TestGetLXCMachineStatus(VNetTestCase):
    def setUp(self) -> None:
        self.machine = Mock()
        self.lxd_client = self.set_up_patch("vnet_manager.operations.machine.get_lxd_client")
        self.lxd_client.return_value = self.machine

    def test_get_lxc_machine_calls_lxd_client(self):
        get_lxc_machine_status("test")
        self.lxd_client.assert_called_once_with()

    def test_get_lxc_machine_status_calls_get_method(self):
        get_lxc_machine_status("test")
        self.machine.containers.get.assert_called_once_with("test")

    def test_get_lxc_machine_status_returns_list_with_status_of_container(self):
        self.machine.containers.get.return_value.status = "banaan"
        self.assertEqual(get_lxc_machine_status("test"), ["test", "banaan", "LXC"])

    def test_get_lxc_machine_status_returns_na_on_not_found_exception(self):
        self.machine.containers.get.side_effect = NotFound(response="blaap")
        self.assertEqual(get_lxc_machine_status("test"), ["test", "NA", "LXC"])


class TestWaitForLXCMachineStatus(VNetTestCase):
    def setUp(self) -> None:
        self.machine = MagicMock()
        self.machine.state.return_value.status = "123"
        self.sleep = self.set_up_patch("vnet_manager.operations.machine.sleep")

    def test_wait_for_lxc_machine_status_calls_state(self):
        wait_for_lxc_machine_status(self.machine, "123")
        self.machine.state.assert_called_once_with()

    def test_wait_for_lxc_machine_status_does_not_call_sleep_if_state_correct(self):
        wait_for_lxc_machine_status(self.machine, "123")
        self.assertFalse(self.sleep.called)

    def test_wait_for_lxc_machine_status_raises_timeout_error_if_right_status_was_not_returned(self):
        self.machine.state.return_value.status = "456"
        with self.assertRaises(TimeoutError):
            wait_for_lxc_machine_status(self.machine, "123")
        self.assertTrue(self.sleep.called)

    def test_wait_for_lxc_machine_status_deals_with_weird_capitals(self):
        self.machine.state.return_value.status = "RuNNING"
        wait_for_lxc_machine_status(self.machine, "rUNNing")


class TestChangeMachineStatus(VNetTestCase):
    def setUp(self) -> None:
        self.change_lxc_machine_status = self.set_up_patch("vnet_manager.operations.machine.change_lxc_machine_status")

    def test_change_machine_status_raises_not_implemented_error_when_invalid_status(self):
        with self.assertRaises(NotImplementedError):
            change_machine_status(settings.CONFIG, status="blaap")

    def test_change_machine_status_calls_change_lxc_machine_status_with_machines_from_config(self):
        change_machine_status(settings.CONFIG)
        calls = [call(m, status="stop") for m in settings.CONFIG["machines"].keys()]
        self.change_lxc_machine_status.assert_has_calls(calls)

    def test_change_machine_status_calls_change_lxc_machine_status_only_with_given_machine_list(self):
        machines = ["router100"]
        change_machine_status(settings.CONFIG, machines=machines)
        self.change_lxc_machine_status.assert_called_once_with(machines[0], status="stop")

    def test_change_machine_status_calls_change_lxc_machine_status_with_different_status(self):
        change_machine_status(settings.CONFIG, status="start")
        calls = [call(m, status="start") for m in settings.CONFIG["machines"].keys()]
        self.change_lxc_machine_status.assert_has_calls(calls)

    def test_change_machine_status_skips_non_existent_machines(self):
        machines = ["banaan1"]
        change_machine_status(settings.CONFIG, machines=machines)
        self.assertFalse(self.change_lxc_machine_status.called)


class TestChangeLXCMachineStatus(VNetTestCase):
    def setUp(self) -> None:
        self.lxd_client = self.set_up_patch("vnet_manager.operations.machine.get_lxd_client")
        self.client = Mock()
        self.machine = Mock()
        self.lxd_client.return_value = self.client
        self.client.containers.get.return_value = self.machine
        self.sleep = self.set_up_patch("vnet_manager.operations.machine.sleep")
        self.wait_for_lxc_machine_status = self.set_up_patch("vnet_manager.operations.machine.wait_for_lxc_machine_status")

    def test_change_lxc_machine_status_calls_lxd_client(self):
        change_lxc_machine_status("banaan")
        self.lxd_client.assert_called_once_with()

    def test_change_lxc_machine_status_calls_sleep(self):
        change_lxc_machine_status("banaan")
        self.sleep.assert_called_once_with(1)

    def test_change_lxc_machine_status_calls_containers_get(self):
        change_lxc_machine_status("banaan")
        self.client.containers.get.assert_called_once_with("banaan")

    def test_change_lxc_machine_status_calls_machine_stop_by_default(self):
        change_lxc_machine_status("banaan")
        self.machine.stop.assert_called_once_with()

    def test_change_lxc_machine_status_does_not_call_start_by_default(self):
        change_lxc_machine_status("banaan")
        self.assertFalse(self.machine.start.called)

    def test_change_lxc_machine_status_deals_with_not_found_error(self):
        self.client.containers.get.side_effect = NotFound(response="blaap")
        change_lxc_machine_status("banaan")
        self.assertFalse(self.machine.stop.called)
        self.assertFalse(self.machine.start.called)
        self.assertFalse(self.wait_for_lxc_machine_status.called)

    def test_change_lxc_machine_status_call_start_when_passed(self):
        change_lxc_machine_status("banaan", status="start")
        self.machine.start.assert_called_once_with(wait=True)

    def test_change_lxc_machine_status_does_not_call_stop_when_start_passed(self):
        change_lxc_machine_status("banaan", status="start")
        self.assertFalse(self.machine.stop.called)

    def test_change_lxc_machine_status_calls_wait_for_lxc_machine_status_with_stopped(self):
        change_lxc_machine_status("banaan", status="stop")
        self.wait_for_lxc_machine_status.assert_called_once_with(self.machine, "Stopped")

    def test_change_lxc_machine_status_calls_wait_for_lxc_machine_status_with_running(self):
        change_lxc_machine_status("banaan", status="start")
        self.wait_for_lxc_machine_status.assert_called_once_with(self.machine, "Running")

    def test_change_lxc_machine_status_catches_timeout_error(self):
        self.wait_for_lxc_machine_status.side_effect = TimeoutError()
        change_lxc_machine_status("banaan")


class TestCreateMachines(VNetTestCase):
    def setUp(self) -> None:
        self.create_lxc_machines_from_base_image = self.set_up_patch("vnet_manager.operations.machine.create_lxc_machines_from_base_image")

    def test_create_machines_calls_create_lxc_machines_with_config_machines(self):
        create_machines(settings.CONFIG)
        self.create_lxc_machines_from_base_image.assert_called_once_with(settings.CONFIG, settings.CONFIG["machines"].keys())

    def test_create_machines_calls_create_lxc_machine_with_custom_machine_list(self):
        create_machines(settings.CONFIG, machines=["test1", "test2"])
        self.create_lxc_machines_from_base_image.assert_called_once_with(settings.CONFIG, ["test1", "test2"])
