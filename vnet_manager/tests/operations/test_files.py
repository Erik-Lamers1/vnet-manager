from copy import deepcopy
from unittest.mock import call
from os.path import join

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.files import put_files_on_machine, select_files_and_put_on_machine
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
