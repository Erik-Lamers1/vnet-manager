from copy import deepcopy
from unittest.mock import call

from vnet_manager.tests import VNetTestCase
from vnet_manager.operations.files import put_files_on_machine
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
