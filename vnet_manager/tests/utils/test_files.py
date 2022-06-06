from unittest.mock import mock_open, patch

from vnet_manager.tests import VNetTestCase
from vnet_manager.utils.files import get_yaml_files_from_disk_path, get_yaml_content, write_file_to_disk

DATA = """---
test: "test"
        """


class TestGetYAMLContent(VNetTestCase):
    def setUp(self) -> None:
        self.isfile = self.set_up_patch("vnet_manager.utils.files.isfile")

    @patch("builtins.open", new_callable=mock_open, read_data=DATA)
    def test_get_yaml_content_calls_isfile(self, _):
        get_yaml_content("path")
        self.isfile.assert_called_once_with("path")

    @patch("builtins.open", new_callable=mock_open, read_data=DATA)
    def test_get_yaml_content_opens_path(self, open_mock):
        get_yaml_content("path")
        open_mock.assert_called_once_with("path", "r", encoding="utf-8")

    @patch("builtins.open", new_callable=mock_open, read_data=DATA)
    def test_get_yaml_content_returns_parsed_yaml(self, _):
        content = get_yaml_content("path")
        self.assertIn("test", content)
        self.assertEqual(content["test"], "test")


class TestWriteFileToDisk(VNetTestCase):
    @patch("builtins.open", new_callable=mock_open)
    def test_write_file_to_disk_opens_path(self, open_mock):
        write_file_to_disk("path", DATA)
        open_mock.assert_called_once_with("path", "w", encoding="utf-8")

    @patch("builtins.open", new_callable=mock_open)
    def test_write_file_to_disk_calls_write_function(self, open_mock):
        write_file_to_disk("path", DATA)
        handle = open_mock()
        handle.write.assert_called_once_with(DATA)


class TestGetYAMLFilesFromDiskPath(VNetTestCase):
    def setUp(self) -> None:
        self.walk = self.set_up_patch("vnet_manager.utils.files.walk")
        self.walk.return_value = [
            ("/foo", ("bar",), ("baz",)),
            ("/foo/bar", (), ("spam.yaml", "eggs.yml", "hoi.txt")),
        ]

    def test_get_yaml_files_from_disk_path_calls_walk(self):
        get_yaml_files_from_disk_path("path")
        self.walk.assert_called_once_with("path")

    def test_get_yaml_files_from_disk_path_returns_list(self):
        self.assertIsInstance(get_yaml_files_from_disk_path("path"), list)

    def test_get_yaml_files_from_disk_path_returns_yaml_files_in_path(self):
        ret = get_yaml_files_from_disk_path("path")
        self.assertEqual(ret, ["/foo/bar/spam.yaml", "/foo/bar/eggs.yml"])

    def test_get_yaml_files_from_disk_path_excludes_filename(self):
        ret = get_yaml_files_from_disk_path("path", excludes_files=["spam.yaml"])
        self.assertEqual(ret, ["/foo/bar/eggs.yml"])

    def test_get_yaml_files_from_disk_path_excludes_path_and_filename(self):
        ret = get_yaml_files_from_disk_path("path", excludes_files=["/foo/bar/spam.yaml"])
        self.assertEqual(ret, ["/foo/bar/eggs.yml"])
