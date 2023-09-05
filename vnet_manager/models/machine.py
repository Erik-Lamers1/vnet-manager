from typing import Literal, List

from pydantic import BaseModel

from vnet_manager.models.interface import InterfaceModel


class MachineModel(BaseModel):
    name: str
    machine_type: Literal["host", "router"]
    interfaces: List[InterfaceModel]
    vlans: str  # TODO: erikl
