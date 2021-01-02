from .base import *

# /dev/log doesn't exist everywhere
del LOGGING["handlers"]["syslog"]["address"]

# Fixture config
CONFIG = {
    "switches": 2,
    "machines": {
        "router100": {
            "type": "router",
            "interfaces": {"eth12": {"ipv4": "192.168.0.2/24", "ipv6": "fd00:12::2/64", "mac": "00:00:00:00:01:11", "bridge": 0}},
            "vlans": {"vlan.100": {"id": 100, "link": "eth12", "addresses": ["10.0.100.1/24"]},},
            "files": {"router100": "/etc/frr/"},
        },
        "router101": {
            "type": "router",
            "interfaces": {
                "eth12": {"ipv4": "192.168.0.1/24", "ipv6": "fd00:12::1/64", "mac": "00:00:00:00:02:12", "bridge": 0},
                "eth23": {"ipv4": "10.0.0.1/8", "ipv6": "fd00:23::1/64", "mac": "00:00:00:00:02:22", "bridge": 1},
            },
            "files": {"router101": "/etc/frr/"},
        },
        "host102": {
            "type": "host",
            "interfaces": {"eth23": {"ipv4": "10.0.0.2/8", "ipv6": "fd00:23::2/64", "mac": "00:00:00:00:03:23", "bridge": 1}},
            "files": {"host102": "/etc/frr/"},
        },
    },
    "veths": {"vnet-veth1": {"bridge": "vnet-br1", "stp": True}, "vnet-veth0": {"peer": "vnet-veth1", "bridge": "vnet-br0", "stp": False},},
}

VALIDATED_CONFIG = {
    "switches": 2,
    "machines": {
        "router100": {
            "type": "router",
            "interfaces": {"eth12": {"ipv4": "192.168.0.2/24", "ipv6": "fd00:12::2/64", "mac": "00:00:00:00:01:11", "bridge": 0}},
            "files": {"/root/vnet-manager/config/ripng/router100": "/etc/frr/"},
        },
        "router101": {
            "type": "router",
            "interfaces": {
                "eth12": {"ipv4": "192.168.0.1/24", "ipv6": "fd00:12::1/64", "mac": "00:00:00:00:02:12", "bridge": 0},
                "eth23": {"ipv4": "10.0.0.1/8", "ipv6": "fd00:23::1/64", "mac": "00:00:00:00:02:22", "bridge": 1},
            },
            "files": {"/root/vnet-manager/config/ripng/router101": "/etc/frr/"},
        },
        "host102": {
            "type": "host",
            "interfaces": {"eth23": {"ipv4": "10.0.0.2/8", "ipv6": "fd00:23::2/64", "mac": "00:00:00:00:03:23", "bridge": 1}},
        },
    },
    "veths": {
        "vnet-veth3": {"bridge": "vnet-br2", "stp": True},
        "vnet-veth2": {"peer": "vnet-veth3", "bridge": "vnet-br0"},
        "vnet-veth1": {"bridge": "vnet-br1", "stp": True},
        "vnet-veth0": {"peer": "vnet-veth1", "bridge": "vnet-br0", "stp": True},
        "vnet-veth5": {"bridge": "vnet-br2"},
        "vnet-veth4": {"peer": "vnet-veth5", "bridge": "vnet-br1"},
    },
    "config_dir": "/root/vnet-manager/config/ripng",
}

# Speed up testing
LXC_MAX_STATUS_WAIT_ATTEMPTS = 2
