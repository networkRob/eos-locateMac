#!/usr/bin/python
#
# Copyright (c) 2018, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#  - Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#  - Neither the name of Arista Networks nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# locateMac
#
#    Written by:
#       Rob Martin, Arista Networks
#
"""
DESCRIPTION
A Python script for searching the local and then remote switches for a MAC address.
An alias can be created within EOS to execute the command
INSTALLATION
1. Copy the script to /mnt/flash on any switches that the command can be initiated from
2. Change values of switch_username and switch_password to valid account credentials for the switches
3. Create an EOS alias command

CAVEATS
1. Only finds and returns a match if the port the MAC address is on does not participate in LLDP
"""
__author__ = 'rmartin'
__version__ = '1.1'
from jsonrpclib import Server
import sys
from pprint import pprint as pp

dict_nodes = {}
dict_all_mac_matches = {}

switch_username = 'arista'
switch_password = 'arista'
checked_switches = []
search_devices = []
SEARCH_STATUS = False

#==========================================
# Begin Class Declaration
#==========================================

class SwitchCon:
    def __init__(self,ip,s_username,s_password):
        self.ip = ip
        self.username = s_username
        self.password = s_password
        self.server = self._create_switch()
        self.hostname = self._get_hostname()
        self.lldp_neighbors = self._add_lldp_neighbors()
        self.mac_entry = {}  
        if self.ip == 'localhost':
            self._get_localhost_ip()

    def _get_localhost_ip(self):
        for r1 in self.run_commands(['show management api http-commands'])[0]['urls']:
            if 'unix' not in r1:
                checked_switches.append(r1[r1.find('//')+2:r1.rfind(':')])

    def _create_switch(self):
        "This command will create a jsonrpclib Server object for the switch"
        target_switch = Server('https://%s:%s@%s/command-api'%(self.username,self.password,self.ip))
        return(target_switch)

    def run_commands(self,commands):
        "This command will send the commands to the targeted switch and return the results"
        switch_response = self.server.runCmds(1,commands)
        return(switch_response)

    def add_mac(self,mac,intf,vlan):
        self.mac_entry[mac] = {'interface':intf,'vlan':vlan}

    def _get_hostname(self):
        return(self.run_commands(['show hostname'])[0]['hostname'])

    def _add_lldp_neighbors(self):
        dict_lldp = {}
        lldp_results = self.run_commands(['show lldp neighbors detail'])[0]['lldpNeighbors']
        for r1 in lldp_results:
            if lldp_results[r1]['lldpNeighborInfo']:
                l_base = lldp_results[r1]['lldpNeighborInfo'][0]
                dict_lldp[r1] = {'neighbor':l_base['systemName'],'ip':l_base['managementAddresses'][0]['address'],'remote':l_base['neighborInterfaceInfo']['interfaceId'],'bridge':l_base['systemCapabilities']['bridge'],'router':l_base['systemCapabilities']['router']}
        return(dict_lldp)

    def get_lldp_br(self):
        "Returns a dictionary of LLDP neighbors that are bridges and routers"
        tmp_dict = {}
        for r1 in self.lldp_neighbors:
            if self.lldp_neighbors[r1]['bridge'] and self.lldp_neighbors[r1]['router']:
                tmp_dict[r1] = self.lldp_neighbors[r1]
        return(tmp_dict)
            
        

#==========================================
# End Class Declaration
#==========================================
# Begin Function Declarations
#==========================================


def format_MAC(mac_string):
    "Function to format a string with ':'"
    tmp_mac = mac_string.replace('.','')
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


def print_output(data):
    print('\nMAC Address\tHostname\tInterface\tVLAN').expandtabs(20)
    print('------------------\t---------\t----------\t---------').expandtabs(20)
    print('%s\t%s\t%s\t%s\n'%(data)).expandtabs(20)

def query_switch(switch_con,new_mac_search):
    response_current_switch = switch_con.run_commands(['show mac address-table | include %s'%new_mac_search])
    #Check to see if a response was returned for the 'show mac address-table command'
    if response_current_switch[0]:
        mac_response = response_current_switch[0]['unicastTable']['tableEntries']
        #Iterate through all unicast table entries
        for r1 in mac_response:
            if new_mac_search in r1['macAddress']:
                if 'Port-Channel' in r1['interface']:
                    port_details = switch_con.run_commands(['show interfaces %s'%r1['interface']])
                    if port_details[0]: #Verify a response was generated
                        intf_members = [] #Temp variable to contain interfaces within a port-channel
                        for r2 in port_details[0]['interfaces'][r1['interface']]['memberInterfaces']:
                            if 'Peer' not in r2:
                                intf_members.append(r2)
                        switch_con.add_mac(r1['macAddress'],intf_members,r1['vlanId'])
                else:
                    switch_con.add_mac(r1['macAddress'],[r1['interface']],r1['vlanId'])

def search_results(switch_object):
    "Function to take the search results and evaluate the data"
    mac_switch_result = None
    if switch_object.mac_entry:
        for r1 in switch_object.mac_entry:
            for r2 in switch_object.mac_entry[r1]['interface']:
                #Evaluate if the interface and MAC was found on a LLDP neighbor entry
                if r2 not in switch_object.lldp_neighbors:
                    SEARCH_STATUS = True
                    mac_switch_result = (r1,switch_object.hostname,r2,switch_object.mac_entry[r1]['vlan'])
                    print('Found Match')
                    return SEARCH_STATUS, mac_switch_result
                elif r2 in switch_object.lldp_neighbors:
                    SEARCH_STATUS = False
                    remote_ip = switch_object.lldp_neighbors[r2]['ip']
                    if remote_ip not in checked_switches and remote_ip not in search_devices:
                        search_devices.append(switch_object.lldp_neighbors[r2]['ip'])
                    return SEARCH_STATUS, mac_switch_result
                else:
                    for r3 in switch_object.lldp_neighbors:
                        remote_ip = switch_object.lldp_neighbors[r3]['ip']
                        if remote_ip not in checked_switches and remote_ip not in search_devices:
                            search_devices.append(remote_ip)
                    SEARCH_STATUS = False
                    return SEARCH_STATUS, mac_switch_result
    else:
        for r1 in switch_object.lldp_neighbors:
            remote_ip = switch_object.lldp_neighbors[r1]['ip']
            if remote_ip not in checked_switches and remote_ip not in search_devices:
                search_devices.append(remote_ip)
        SEARCH_STATUS = False
        return SEARCH_STATUS, mac_switch_result
            
        

#==========================================
# End Function Declarations
#==========================================
# Begin Main Function
#==========================================


def main(mac_to_search):
    "Main script to get started"
    #Reformat MAC search string
    if '.' in mac_to_search:
        new_mac_search = format_MAC(mac_to_search)
    elif ':' in mac_to_search:
        new_mac_search = mac_to_search
    else:
        new_mac_search = format_MAC(mac_to_search)
    print('Checking the local switch')
    current_switch = SwitchCon('localhost',switch_username,switch_password)
    query_switch(current_switch,new_mac_search)
    #Iterate through mac entries found
    SEARCH_STATUS, mac_switch_result = search_results(current_switch)
    for r1 in search_devices:
        if r1 not in checked_switches:
            print('Checking %s'%r1)
            checked_switches.append(r1)
            remote_switch = SwitchCon(r1,switch_username,switch_password)
            query_switch(remote_switch,new_mac_search)
            SEARCH_STATUS, mac_switch_result = search_results(remote_switch)
    if SEARCH_STATUS:
        print_output(mac_switch_result)
    else:
        print("No matches found for %s" %mac_to_search)

#==========================================
# End Main Function
#==========================================

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print('MAC Address not provided')
