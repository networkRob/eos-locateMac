# Locate a MAC Address within the environment
#### Version 2.0
In this version, a queried MAC address will return a 'Found' result for ports that have LLDP enabled but are not an Arista switch.

#### Version 1.2
This script will query the local switch and any remote switches (if necessary) to locate the queried MAC address.  If a match is found, it will report back the Switch, MAC, VLAN, and Interface.

### Setup
This script will need to be copied to any switch that this command will be sourced from.  Does not need to be copied on any remote switches that will be queried.

    /mnt/flash

Each device within the environment will need to have eAPI access configured.  This can be done with the following commands.  Within EOS, enter the following commands:

    # config
    (config)# management api http-commands
    (config)# no shut
    (config)# end

On each device that will have this script ran from, within EOS, enter the following commands:

    # config
    (config)# alias findmac bash /mnt/flash/locateMac.py %1
    (config)# end
    # write