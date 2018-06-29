# Locate a MAC Address within the environment
This script will query the local switch and any remote switches (if necessary) to locate teh queried MAC address.  If a match is found, it will report back the Switch, MAC, VLAN, and Interface.

### Setup
This script will need to be copied to any switch that this command will be sourced from.  Does not need to be copied on any remote switches that will be queried.

    /mnt/flash

Each device within the environment will need to have eAPI access configured.  This can be done with the following commands.  Within EOS, enter the following commands:

    # config
    (config)# management api http-commands
    (config)# no shut
    (config)# end


### Documentation to Complete:
1. Add in the setup necessary to create an alias that will take a MAC string
2. Additional documentation based off the completion of the script