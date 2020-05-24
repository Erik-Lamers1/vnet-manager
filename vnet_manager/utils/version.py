from pkg_resources import require

from vnet_manager.conf import settings


def show_version():
    print(
        """
VNet manager version {}
""".format(
            require(settings.PYTHON_PACKAGE_NAME)[0].version
        )
    )
