from copy import deepcopy
from unittest.mock import call, patch, mock_open, MagicMock
from os.path import join
from pylxd.exceptions import NotFound

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.files import put_files_on_machine, select_files_and_put_on_machine, place_file_on_lxc_machine
from vnet_manager.conf import settings


class TestPutFilesOnMachine(VNetTestCase):
    def setUp(self) -> None:
        # Use VALIDATED_CONFIG because here the files part has been expanded to the absolute paths
        self.config = deepcopy(settings.VALIDATED_CONFIG)
        self.select_and_put_on_machine = self.set_up_patch("vnet_manager.operations.files.select_files_and_put_on_machine")

    def test_put_files_on_machine_gets_file_paths_from_config_and_calls_select_files_and_put_on_machine(self):
        calls = [
            call(name, data["files"], settings.MACHINE_TYPE_PROVIDER_MAPPING[data["type"]])
            for name, data in self.config["machines"].items()
            if "files" in data
        ]
        put_files_on_machine(self.config)
        self.select_and_put_on_machine.assert_has_calls(calls)

    def test_put_files_on_machine_does_not_call_select_files_and_put_on_machine_when_there_are_no_machines_with_files(self):
        del self.config["machines"]["router100"]
        del self.config["machines"]["router101"]
        put_files_on_machine(self.config)
        self.assertFalse(self.select_and_put_on_machine.called)


class TestSelectFilesAndPutOnMachine(VNetTestCase):
    def setUp(self) -> None:
        self.logger = self.set_up_patch("vnet_manager.operations.files.logger")
        self.is_dir = self.set_up_patch("vnet_manager.operations.files.isdir")
        self.is_dir.return_value = True
        self.is_file = self.set_up_patch("vnet_manager.operations.files.isfile")
        self.is_file.return_value = True
        self.place_file_on_lxc_machine = self.set_up_patch("vnet_manager.operations.files.place_file_on_lxc_machine")
        self.list_dir = self.set_up_patch("vnet_manager.operations.files.listdir")
        self.list_dir.return_value = ["file1", "file2", "file3"]
        self.machine = "router100"
        self.files = settings.VALIDATED_CONFIG["machines"]["router100"]["files"]

    def test_select_files_and_put_on_machine_calls_check_methods_to_check_for_file_or_dir(self):
        self.is_dir.return_value = False
        select_files_and_put_on_machine(self.machine, self.files, "lxc")
        self.is_dir.assert_called_once_with(next(iter(self.files)))
        self.is_file.assert_called_once_with(next(iter(self.files)))

    def test_select_files_and_put_on_machine_put_a_single_file_on_machine(self):
        self.is_dir.return_value = False
        select_files_and_put_on_machine(self.machine, self.files, "lxc")
        self.place_file_on_lxc_machine.assert_called_once_with(self.machine, next(iter(self.files)), next(iter(self.files.values())))

    def test_select_files_and_put_on_machine_calls_listdir_function(self):
        select_files_and_put_on_machine(self.machine, self.files, "lxc")
        self.list_dir.assert_called_once_with(next(iter(self.files)))

    def test_select_files_and_put_on_machine_calls_place_method_for_each_file_in_dir(self):
        select_files_and_put_on_machine(self.machine, self.files, "lxc")
        calls = [
            call(self.machine, join(next(iter(self.files)), file), join(next(iter(self.files.values())), file))
            for file in self.list_dir.return_value
        ]
        self.place_file_on_lxc_machine.assert_has_calls(calls)

    def test_select_files_and_put_on_machine_logs_error_if_file_is_not_a_dir_or_file(self):
        self.is_dir.return_value = False
        self.is_file.return_value = False
        select_files_and_put_on_machine(self.machine, self.files, "lxc")
        self.logger.error.assert_called_once_with(
            "Tried to select file {} for copying, but it is neither a file nor a directory".format(next(iter(self.files)))
        )


class TestPlaceFileOnLXCContainer(VNetTestCase):
    def setUp(self) -> None:
        self.get_lxd_client = self.set_up_patch("vnet_manager.operations.files.get_lxd_client")
        self.client = MagicMock()
        self.machine = MagicMock()
        self.get_lxd_client.return_value.containers.get.return_value = self.machine
        self.is_file = self.set_up_patch("vnet_manager.operations.files.isfile")
        self.host_file_p = "/root/host"
        self.guest_file_p = "/root/guest"

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_place_file_on_lxc_machine_calls_lxd_client(self, _):
        place_file_on_lxc_machine("router100", self.host_file_p, self.guest_file_p)
        self.get_lxd_client.assert_called_once_with()

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_place_file_on_lxc_machine_calls_open(self, open_mock):
        place_file_on_lxc_machine("router100", self.host_file_p, self.guest_file_p)
        open_mock.assert_called_once_with(self.host_file_p, "r")

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_place_file_on_lxc_machine_calls_open_read_function(self, open_mock):
        place_file_on_lxc_machine("router100", self.host_file_p, self.guest_file_p)
        handle = open_mock()
        handle.read.assert_called_once_with()

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_place_file_on_lxc_machine_does_nothing_if_container_not_found(self, open_mock):
        self.get_lxd_client.side_effect = NotFound(response=b"response")
        place_file_on_lxc_machine("router100", self.host_file_p, self.guest_file_p)
        self.assertFalse(open_mock.called)

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_place_file_on_lxc_machine_does_nothing_if_file_is_not_a_file(self, open_mock):
        self.is_file.return_value = False
        place_file_on_lxc_machine("router100", self.host_file_p, self.guest_file_p)
        self.assertFalse(open_mock.called)

    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_place_file_on_lxc_machine_calls_files_put_method_on_machine(self, _):
        place_file_on_lxc_machine("router100", self.host_file_p, self.guest_file_p)
        self.machine.files.put.assert_called_once_with(self.guest_file_p, "data")
