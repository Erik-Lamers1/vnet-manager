import sys
from logging import getLogger
from os import EX_NOPERM, environ
from typing import Sequence

from vnet_manager.conf import settings
from vnet_manager.log import setup_console_logging, get_logging_verbosity
from vnet_manager.actions.manager import ActionManager
from vnet_manager.utils.user import check_for_root_user
from vnet_manager.argeparser import parse_vnet_args

logger = getLogger(__name__)


def main(args: Sequence = None) -> int:
    """
    Program entry point
    :param list args: The pre-cooked arguments to pass to the ArgParser
    :return int: exit_code
    """
    args = vars(parse_vnet_args(args))
    # Set the VNET_FORCE variable, if --yes is given this will answer yes to all questions
    environ[settings.VNET_FORCE_ENV_VAR] = "true" if args.get("yes") else "false"
    # Setup logging
    setup_console_logging(verbosity=get_logging_verbosity(verbose=args["verbose"], quite=args["quite"]))
    # Most VNet operation require root. So, do a root check
    if not check_for_root_user():
        logger.critical("This program should only be run as root")
        return EX_NOPERM
    # Let the action manager handle the rest
    manager = ActionManager(
        config_path=args.get("config"),
        sniffer=args.get("sniffer", False),
        base_image=args.get("base_image", False),
        no_hosts=args.get("no_hosts", False),
        provider=args.get("provider"),
        pcap_dir=args.get("pcap_dir", settings.VNET_SNIFFER_PCAP_DIR),
    )
    if args.get("machines"):
        manager.machines = args["machines"]
    # Status is renamed to show to make sure we execute the right action
    if args["action"] == "status":
        args["action"] = "show"
    return manager.execute(args["action"])


if __name__ == "__main__":
    sys.exit(main())
