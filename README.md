# Locate a MAC Address within the environment
#### Version 3.2
Disabled SSL Verification where it would throw an error in 4.21.1F.
#### Version 3.1
Updated Setup Documentation to take into account enviroments with VRFs enabled.
##### Features
- Ability to query local switch and remote switches that have VRFs enabled. (See updated setup documentation)
- Added description for MAC addresses with `Not Found` status results

        Arista#findmac c52a
        Searching....

        MAC Address         Hostname            Interface           VLAN                Status
        ------------------  ---------           ----------          ---------           ---------
        00:0c:29:aa:c5:2a   7280-sw-01         Ethernet47          50                  *Not Found
        
        *Last Switch and Port to report this MAC Address. Check device connected to this port.

##### Fixes
- Added in logic to prevent the script from failing when it tries to add a switch not capable of `virtual-router`.
#### Version 3.0
Updated outputs that consolidates non-eAPI enabled Arista switches to the end.  If the script hangs on the output of the following for a couple of minutes.

    LM-SW04#findmac b660
    Searching....

This is the script waiting for the timeout to occur on the eAPI call.  This can be escaped sooner by performing a `ctrl-c` on the keyboard.  This will skip the current non-eapi switch and continue on.

#### Version 2.4
Cleaned up some un-used code. 
##### Fixes
- Corrected an issue that the script tried querying a non-Arista switch.
#### Version 2.3
##### Fixes
- Corrected an issue where the script would fail on LLDP neighbor info that was blank or missing `systemCapabilites` key.
- Added a check that will stop the script and report back if the local switch does not have eAPI enabled.
#### Version 2.2
Corrected an issue where no results would return on a query include a `.`.  
#### Version 2.1
This release adds the below functionality and fixes:
##### Features
- Added functionality to query against virtual MAC addresses.
- If virtual MAC address is queried against, returns all switches with that MAC configured
- Ability to search on any MAC address length.
##### Fixes
- Resolved an issue where MAC search query was case sensitive and wouldn't return results with upper case characters.


#### Version 2.0
In this version, a queried MAC address will return a 'Found' result for ports that have LLDP enabled but are not an Arista switch.


#### Version 1.2
This script will query the local switch and any remote switches (if necessary) to locate the queried MAC address.  If a match is found, it will report back the Switch, MAC, VLAN, and Interface.


## Setup

#### All Environments
This script will need to be copied to any switch that this command will be sourced from.  Does not need to be copied on any remote switches that will be queried.

    /mnt/flash

#### Non-VRF Enabled Environments
Each device within the environment will need to have eAPI access configured.  This can be done with the following commands.  Within EOS, enter the following commands:

    Arista#config
    Arista(config)#management api http-commands
    Arista(config)#no shut
    Arista(config)#end

On each device that will have this script ran from, within EOS, enter the following commands:

    Arista#config
    Arista(config)#alias findmac bash /mnt/flash/locateMac.py %1
    Arista(config)#end
    Arista#write

#### VRF Enabled Environments
If VRFs are utilized within the environment, each device will need to have eAPI access configured for the management VRF.  In the examples below, the name of the VRF is `MGMT`.  If it differs in the environment, replace `MGMT` with the name of the VRF.

This can be done with the following commands.  Within EOS, enter the following commands:

    Arista#config
    Arista(config)#management api http-commands
    Arista(config)#no shut
    Arista(config)#vrf MGMT
    Arista(config)#no shut
    Arista(config)#end

If the switches within the evironment utilizes a VRF for the `ma1` interface, the following configuration will need to be ran on all switches within the environment.  

    Arista(config)#lldp management-address vrf MGMT

On each device that will have this script ran from, within EOS, enter the following commands: (If the VRF name is different replace `MGMT` in the section from `ns-MGMT` with the name of the VRF).

    Arista#config
    Arista(config)#alias findmac bash sudo ip netns exec ns-MGMT /mnt/flash/locateMac.py %1
    Arista(config)#end
    Arista#write