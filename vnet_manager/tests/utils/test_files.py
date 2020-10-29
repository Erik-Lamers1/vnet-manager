from vnet_manager.tests import VNetTestCase
from vnet_manager.utils.files import get_yaml_files_from_disk_path


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

    def test_get_yaml_files_from_disk_path_excludes_path(self):
        ret = get_yaml_files_from_disk_path("path", excludes_files=["/foo/bar"])
        self.assertEqual(ret, [])

    def test_get_yaml_files_from_disk_path_excludes_path_and_filename(self):
        ret = get_yaml_files_from_disk_path("path", excludes_files=["/foo/bar/spam.yaml"])
        self.assertEqual(ret, ["/foo/bar/eggs.yml"])
