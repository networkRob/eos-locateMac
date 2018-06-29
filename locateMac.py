#!/usr/bin/python

"""
This script will take an input of a MAC Address or partial MAC Address.  Steps it will perform
1. Search local switch for MAC
2. If not on local but neighboring switch, will query the neighbor switch
3. When match is found, it will report back the switch, MAC, VLAN, Port

Written by Robert Martin.

USAGE:

create an alias within EOS

{Insert Usage Information}

"""

from jsonrpclib import Server
from sys import argv

dict_nodes = {}
dict_all_mac_matches = {}

switch_username = 'arista'
switch_password = 'arista'

def create_switch(switch_ip):
    "This command will create a jsonrpclib Server object for the switch"
    target_switch = Server('https://%s:%s@%s/command-api'%(switch_username,switch_password,switch_ip))
    return(target_switch)

def run_commands(switch_target,commands):
    "This command will send the commands to the targeted switch and return the results"
    switch_response = switch_target.runCmds(1,commands)
    return(switch_response)

def format_MAC(mac_string):
    "Function to format a string with ':'"
    tmp_mac = mac_string('.','')
    mac_len = len(tmp_mac)
    if mac_len == 12:
        new_mac_search = "%s%s:%s%s:%s%s:%s%s:%s%s:%s%s" %tuple(tmp_mac)
    elif mac_len >= 10:
        new_mac_search = "%s%s:%s%s:%s%s:%s%s:%s%s" %tuple(tmp_mac)
    elif mac_len >= 8:
        new_mac_search = "%s%s:%s%s:%s%s:%s%s" %tuple(tmp_mac)
    elif mac_len >= 6:
        new_mac_search = "%s%s:%s%s:%s%s" %tuple(tmp_mac)
    elif mac_len >= 4:
        new_mac_search = "%s%s:%s%s" %tuple(tmp_mac)
    elif mac_len >= 2:
        new_mac_search = "%s%s" %tuple(tmp_mac)
    return(new_mac_search)
        
def main(mac_to_search):
    "Main script to get started"
        
    #Reformat MAC search string
    if '.' in mac_to_search:
        new_mac_search = format_MAC(mac_to_search)
    elif ':' in mac_to_search:
        new_mac_search = mac_to_search
    else:
        new_mac_search = format_MAC(mac_to_search)
    
    current_switch = create_switch('localhost')
    response_current_switch = run_commands(current_switch,['enable','show mac address-table | include %s'%new_mac_search,'show lldp neighbors'])
    
    #TODO: Check to see if a match was found on local switch end and report

    #TODO: If match found on remote switch, query remote switch, if round end and report it.  If on remote, repeat queries


if __name__ == '__main__':
    if len(argv) > 1:
        main(argv[1])
    else:
        print('MAC Address not provided')
