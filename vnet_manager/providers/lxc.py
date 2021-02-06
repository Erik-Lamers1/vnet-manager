from pylxd import client


def get_lxd_client(**kwargs) -> client.Client:
    """
    Get an LXC client.Client() with the passed parameters
    :return: pylxd.client.Client()
    """
    return client.Client(**kwargs)
