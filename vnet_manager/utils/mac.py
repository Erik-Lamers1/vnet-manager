from random import randint


def random_mac_generator():
    """
    Generates a random MAC address
    :return: str: The generated MAC address
    """
    # From: https://stackoverflow.com/a/43546406/8632038
    return "00:00:00:%02x:%02x:%02x" % (randint(0, 255), randint(0, 255), randint(0, 255))
