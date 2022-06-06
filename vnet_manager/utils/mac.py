from random import randint


def random_mac_generator() -> str:
    """
    Generates a random MAC address
    :return: str: The generated MAC address
    """
    # From: https://stackoverflow.com/a/43546406/8632038
    # Put 0x02 at the start to make it a locally administered address
    return f"02:00:00:{randint(0, 255):02x}:{randint(0, 255):02x}:{randint(0, 255):02x}"
