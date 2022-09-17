from pylxd.exceptions import ClientConnectionFailed

from vnet_manager.tests import VNetTestCase
from vnet_manager.providers.lxc import get_lxd_client


class TestGetLXDClient(VNetTestCase):
    def setUp(self) -> None:
        self.client = self.set_up_patch("vnet_manager.providers.lxc.client")

    def test_get_lxd_client_calls_client(self):
        get_lxd_client()
        self.client.Client.assert_called_once_with()

    def test_get_lxc_client_calls_client_with_arguments(self):
        get_lxd_client(socket="blaap")
        self.client.Client.assert_called_once_with(socket="blaap")

    def test_get_lxc_client_exits_if_connection_fails(self):
        self.client.Client.side_effect = ClientConnectionFailed
        with self.assertRaises(SystemExit) as e:
            get_lxd_client()
        self.assertEqual(e.exception.code, 1)
