from ipaddress import IPv4Interface, IPv6Interface
from re import fullmatch
from logging import getLogger
from os.path import isdir, isfile, join

from vnet_manager.utils.mac import random_mac_generator
from vnet_manager.conf import settings

logger = getLogger(__name__)


def validate_config(config):
    """
    Validate the vnet config
    Search for required values, some are automatically filled in if missing
    :param dict config: The config provided by get_config()
    :return: bool: True if valid config, False otherwise, dict config: The updated config
    """
    default_message = ". Please check your settings"
    all_ok = True

    # TODO: This is one massive function, split this up into like 3 functions, one for each section
    # Providers
    if "providers" not in config:
        logger.error("Providers dict not found in config, this usually means the default config is not correct" + default_message)
        all_ok = False
    elif not isinstance(config["providers"], dict):
        logger.error("Providers is not a dict, this means the default config is corrupt" + default_message)
        all_ok = False
    else:
        for name, values in config["providers"].items():
            if "supported_operating_systems" not in values:
                logger.error("No supported operating systems found for provider {}".format(name) + default_message)
                all_ok = False
            elif not isinstance(values["supported_operating_systems"], list):
                logger.error("supported_operating_systems for provider {} is not a list".format(name) + default_message)
                all_ok = False
            if "dns-nameserver" not in values or not isinstance(values["dns-nameserver"], str):
                logger.warning("DNS nameserver not correctly set for provider {}. Defaulting to 8.8.8.8".format(name))
                values["dns-nameserver"] = "8.8.8.8"
            if "required_host_packages" not in values or not isinstance(values["required_host_packages"], list):
                logger.warning("Required host packages not correctly set for provider {}. Defaulting to empty list".format(name))
                values["required_host_packages"] = list()
            if "guest_packages" not in values or not isinstance(values["guest_packages"], list):
                logger.warning("Guest packages not correctly set for provider {}. Defaulting to empty list".format(name))
                values["guest_packages"] = list()
            if "base_image" not in values:
                logger.error("No base_image found for provider {}".format(name) + default_message)
                all_ok = False
            elif not isinstance(values["base_image"], dict):
                logger.error("base_image for provider {} is not a string.".format(name) + default_message)
                all_ok = False
            # TODO: Validate base image parameters

    # Switches
    if "switches" not in config:
        logger.error("Config item 'switches' missing" + default_message)
        all_ok = False
    elif not isinstance(config["switches"], int):
        logger.error("Config item 'switches: {}' does not seem to be an integer".format(config["switches"]) + default_message)
        all_ok = False

    # Machines
    if "machines" not in config:
        logger.error("Config item 'machines' missing" + default_message)
        all_ok = False
    elif not isinstance(config["machines"], dict):
        logger.error("Machines config is not a dict, this means the user config is incorrect" + default_message)
        all_ok = False
    else:
        for name, values in config["machines"].items():
            if "type" not in values:
                logger.error("Type not found for machine {}".format(name) + default_message)
                all_ok = False
            elif values["type"] not in settings.SUPPORTED_MACHINE_TYPES:
                logger.error(
                    "Type {} for machine {} unsupported. I only support the following types: {}".format(
                        values["type"], name, settings.SUPPORTED_MACHINE_TYPES
                    )
                    + default_message
                )
                all_ok = False

            # Files
            if "files" in values:
                if not isinstance(values["files"], dict):
                    logger.error("Files directive for machine {} is not a dict".format(name) + default_message)
                    all_ok = False
                else:
                    # Check the files
                    for host_file in values["files"].keys():
                        # First check if the user gave a relative dir from the config dir
                        if isdir(join(config["config_dir"], host_file)) or isfile(join(config["config_dir"], host_file)):
                            logger.debug(
                                "Updating relative host_file path {} to full path {}".format(
                                    host_file, join(config["config_dir"], host_file)
                                )
                            )
                            values["files"][join(config["config_dir"], host_file)] = values["files"].pop(host_file)
                        # Check for absolute paths
                        elif not isdir(host_file) or not isfile(host_file):
                            logger.error(
                                "Host file {} for machine {} does not seem to be a dir or a file".format(host_file, name) + default_message
                            )
                            all_ok = False

            # Interfaces
            if "interfaces" not in values:
                logger.error("Machine {} does not appear to have any interfaces".format(name) + default_message)
                all_ok = False
            elif not isinstance(values["interfaces"], dict):
                logger.error(
                    "The interfaces for machine {} are not given as a dict, this usually means a typo in the config".format(name)
                    + default_message
                )
                all_ok = False
            else:
                for int_name, int_vals in values["interfaces"].items():
                    if "ipv4" not in int_vals:
                        logger.error("ipv4 not found for interface {} on machine {}".format(int_name, name) + default_message)
                        all_ok = False
                    else:
                        # Validate the given IP
                        try:
                            IPv4Interface(int_vals["ipv4"])
                        except ValueError as e:
                            logger.error(
                                "Unable to parse IPv4 address {} for machine {}. Parse error: {}".format(int_vals["ipv4"], name, e)
                            )
                            all_ok = False
                    if "ipv6" not in int_vals:
                        logger.info(
                            "No IPv6 found for interface {} on machine {}, that's okay no IPv6 address will be configured".format(
                                int_name, name
                            )
                        )
                    else:
                        # Validate the given IP
                        try:
                            IPv6Interface(int_vals["ipv6"])
                        except ValueError as e:
                            logger.error(
                                "Unable to parse IPv6 address {} for machine {}. Parse error: {}".format(int_vals["ipv6"], name, e)
                            )
                            all_ok = False
                    if "mac" not in int_vals:
                        logger.info("MAC not found for interface {} on machine {}, generating a random one".format(int_name, name))
                        int_vals["mac"] = random_mac_generator()
                    # From: https://stackoverflow.com/a/7629690/8632038
                    elif not fullmatch(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", int_vals["mac"]):
                        logger.error(
                            "MAC {} for interface {} on machine {}, does not seem to be valid".format(int_vals["mac"], int_name, name)
                            + default_message
                        )
                        all_ok = False
                    if "bridge" not in int_vals:
                        logger.error("bridge keyword missing on interface {} for machine {}".format(int_name, name) + default_message)
                        all_ok = False
                    elif not isinstance(int_vals["bridge"], int) or int_vals["bridge"] > config["switches"] - 1:
                        logger.error(
                            "Invalid bridge number detected for interface {} on machine {}. "
                            "The bridge keyword should correspond to the interface number of the vnet bridge to connect to "
                            "(starting at iface number 0)".format(int_name, name)
                        )
                        all_ok = False
    # Return the results
    return all_ok, config
