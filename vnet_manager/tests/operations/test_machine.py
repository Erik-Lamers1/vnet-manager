from vnet_manager.tests import VNetTestCase
from vnet_manager.conf import settings
from vnet_manager.operations.machine import show_status


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
