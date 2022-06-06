from typing import Any, List, Union
import collections
import importlib
import os

ENV_VAR = "SETTINGS_MODULE"


class Settings(collections.abc.Mapping):
    def __init__(self, settings_module_name: str):
        mod = importlib.import_module(settings_module_name)

        # Assign al values to self
        for setting in filter(lambda x: x.isupper(), dir(mod)):
            setattr(self, setting, getattr(mod, setting))

    def __getitem__(self, item: str) -> Any:
        """Enable dict-like access to the settings"""
        try:
            return getattr(self, item)
        except AttributeError as e:
            raise KeyError(item) from e

    def __iter__(self) -> list:
        # return all upper case variables, but not internals
        return [x for x in dir(self) if x.isupper()]

    def __len__(self) -> int:
        return len(self.__iter__())


settings_module = os.environ.get(ENV_VAR, "vnet_manager.settings.base")

settings = Settings(settings_module)


def import_from_string(val: str, setting_name: str) -> Any:
    # Borrowed from https://github.com/tomchristie/django-rest-framework/blob/0dec36e/rest_framework/settings.py#L169
    """
    Attempt to import a class from a string representation.
    """
    try:
        # Nod to tastypie's use of importlib.
        parts = val.split(".")
        module_path, class_name = ".".join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        msg = f"Could not import '{val}' for setting '{setting_name}'. {e.__class__.__name__}: {e}."
        raise ImportError(msg) from e


def perform_import(val: Any, setting_name: str) -> Union[Any, List[Any]]:
    # Borrowed from https://github.com/tomchristie/django-rest-framework/blob/0dec36e/rest_framework/settings.py#L155
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if isinstance(val, str):
        return import_from_string(val, setting_name)
    if isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val
