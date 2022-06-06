from pkg_resources import require

from vnet_manager.conf import settings


def show_version():
    print(
        f"""
VNet manager version {require(settings.PYTHON_PACKAGE_NAME)[0].version}
"""
    )
