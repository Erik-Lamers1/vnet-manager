# VNet-manager config
VNet-manager works with YAML configs in order to define virtual networks.
- The user config, is passed to the vnet-manager command as an argument.

## User config
The user config defines a virtual network. The hosts, routers and interfaces should be defined in this config.
Below the currently possible user, config options are explained.

```yaml
switches: int  # Switches defines the number of vnet-bridges that should be created.
               # Each machine interface will be connected to one of these bridges.
               # And they should be viewed as simple switches.

machines: dict  # The machine dict defines that vnet machines that are part of this virtual network.
  host1: dict  # This dict defines a vnet machine.
    type: str  # This define what type the machine will be, see `Machine types`
    interfaces: dict  # This dict defines what virtual interfaces should be assigned to a machine.
      eth1: dict  # This dict defines a vnet interface, which is part of a vnet machine.
        ipv4: ipv4_address/cidr  # This IPv4 address will be assigned to the interface (optional).
        ipv6: ipv6_address/cidr  # This IPv6 address will be assigned to the interface (optional).
        mac: mac_address  # This mac address will be assigned to the interface.
        routes: list  # A list of routes to add to this interface, see: https://netplan.io/reference/#routing
        bridge: int  # The bridge number that this interface will be connected to.
                     # Note that counting starts from 0.
                     # So, if you want to connect to the first bridge, this value should be set to 0.
      ethN: ...
    vlans: dict  # This defines the vlan interfaces that will be created on the machine (optional).
      vlan.100: dict  # This defines a vlan interface
        id: int  # The vlan id of this interface.
        link: str  # The parent interface, this must correspond to a interface configured above.
        addresses: list  # The IP addresses to assign to this vlan interface (optional).
      vlan.N: ...
    bridges: dict  # This defines the bridge interfaces that will be created on the machine (optional).
      bridge1:  dict  # This dict defines a bridge interface.
        slaves: list  # A list of interfaces that will be assigned to this bridge.
        ipv4: ipv4_address/cidr  # Assign the following IPv4 address to the bridge (optional).
        ipv6: ipv6_address/cidr  # Assign the following IPv6 address to the bridge (optional).
      bridgeN: ...
    files: dict  # This defines the files that will be copied to the machine (optional).
      host1: str  # Key should be set to the absolute or relative path as seen from the user config.
                      # This can be a directory or a single file.
                      # Value should be set the directory on the machine to copy the file(s) to.
      fileX: ...
  hostN: ...

veths: dict  # Veths can be used to link two vnet bridges together (optional).
             # When two bridges are linked this will create a virtual link between the two bridges.
             # So they can communicate with each other.
  vnet-veth0: dict  # This defines a vnet veth interface
    peer: str  # The name of the other vnet veth interface to peer/link with.
               # A peerage should only be defined once, this can be done on either vnet veth interface.
               # Note, the peerage should be defined before the peered interface is defined.
    bridge: str  # The full name of the vnet bridge to connect this veth interface to.
                 # Note, the vnet bridge prefix can be found in the settings (default: vnet-br).
    stp: bool  # Weather to enable STP on the corresponding bridge interface (optional).
  vnet-vethN: ...
```

### Machine types
The machine type determines the specific configuration that will be placed on the machine. The following machine types are supported:
- Host, simple endpoint, explicitly disables IP forwarding (set in /etc/sysctl.d/)
- Router, IP forwarding enabled (set in /etc/sysctl.d/)

