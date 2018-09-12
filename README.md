# Locate a MAC Address within the environment
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