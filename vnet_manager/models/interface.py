import re
from ipaddress import IPv4Interface, IPv6Interface
from typing import Optional, Union, Literal, List

from pydantic import BaseModel, field_validator, IPvAnyAddress, IPvAnyNetwork, PositiveInt
from vnet_manager.utils import mac


class InterfaceRoute(BaseModel):
    via: IPvAnyAddress
    to: Union[IPvAnyNetwork, Literal["default"]]
    on_link: Optional[bool]
    metric: Optional[PositiveInt]
    type: Optional[str]
    scope: Optional[Literal["global", "link", "host"]]
    table: Optional[PositiveInt]
    mtu: Optional[PositiveInt]


class InterfaceModel(BaseModel):
    name: str
    bridge: int
    mac: str = mac.random_mac_generator()
    ipv4_address: Optional[IPv4Interface]
    ipv6_address: Optional[IPv6Interface]
    routes: Optional[List[InterfaceRoute]]

    @field_validator("mac")
    @classmethod
    def validate_mac(cls, v: str) -> str:
        # From: https://stackoverflow.com/a/7629690/8632038
        assert re.fullmatch(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", v), f"MAC address {v} is not a valid MAC"
        return v
