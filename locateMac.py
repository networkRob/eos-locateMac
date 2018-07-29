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
    switch(config)# alias findmac bash /mnt/flash/locateMac.py %1
    
CAVEATS
1. Only finds and returns a match if the port the MAC address is on does not participate in LLDP
"""
__author__ = 'rmartin'
__version__ = 1.2
from jsonrpclib import Server
from sys import argv

switch_username = 'arista'
switch_password = 'arista'
checked_switches = []
search_devices = []
all_macs = []
all_switches = []

#==========================================
# Begin Class Declaration
#==========================================

class MACHOSTS:
    def __init__(self,mac,vlan,switch,intf):
        self.mac = mac
        self.status = False
        self.switch = switch
        self.interface = intf
        self.vlan = vlan

class SwitchCon:
    def __init__(self,ip,s_username,s_password,s_vend=False):
        if s_vend:
            self.ip = ip
            self.username = s_username
            self.password = s_password
            self.mac_entry = []
            self.server = self._create_switch()
            try:
                self.hostname = self._get_hostname()
                self.STATUS = True
            except:
                self.STATUS = False
            if self.STATUS:
                self.lldp_neighbors = self._add_lldp_neighbors()
                self.system_mac = self._get_system_mac()
                self.lldp_br = self.get_lldp_br()
                if self.ip == 'localhost':
                    self._get_localhost_ip()  
            else:
                print('\nSwitch does not have eAPI enabled\n\n')
        else:
            print('\nDevice %s is not an Arista switch\n\n'%ip)
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
    def add_mac(self,MAC):
        add_code = True
        for r1 in self.mac_entry:
            if MAC.mac == r1.mac:
                add_code = False
        if add_code:
            self.mac_entry.append(MAC)
    def _get_system_mac(self):
        return(self.run_commands(['show version'])[0]['systemMacAddress'])
    def _get_hostname(self):
        return(self.run_commands(['show hostname'])[0]['hostname'])
    def _add_lldp_neighbors(self):
        dict_lldp = {}
        lldp_results = self.run_commands(['show lldp neighbors detail'])[0]['lldpNeighbors']
        for r1 in lldp_results:
            if lldp_results[r1]['lldpNeighborInfo']:
                l_base = lldp_results[r1]['lldpNeighborInfo'][0]
                if 'Arista' in l_base['systemDescription']:
                    a_vend = True
                else:
                    a_vend = False
                dict_lldp[r1] = {'neighbor':l_base['systemName'],'ip':l_base['managementAddresses'][0]['address'],'remote':l_base['neighborInterfaceInfo']['interfaceId'],'bridge':l_base['systemCapabilities']['bridge'],'router':l_base['systemCapabilities']['router'],'Arista':a_vend}
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
    print('\nMAC Address\tHostname\tInterface\tVLAN\tStatus').expandtabs(20)
    print('------------------\t---------\t----------\t---------\t---------').expandtabs(20)
    for r1 in data:
        print_vlans = ''
        r1.vlan.sort()
        for r2 in r1.vlan:
            if print_vlans == '':
                print_vlans = str(r2)
            else:
                print_vlans += ', %s'%str(r2)
        if r1.status:
            print('%s\t%s\t%s\t%s\tFound'%(r1.mac,r1.switch,r1.interface,print_vlans)).expandtabs(20)
        else:
            print('%s\t%s\t%s\t%s\tNot Found'%(r1.mac,r1.switch,r1.interface[0],print_vlans)).expandtabs(20)
    print

def check_all_macs(mac):
    "Checks to see if object has been created for a MAC Address"
    for r1 in all_macs:
        if mac == r1.mac:
            return r1
    else:
        return None

def check_all_mac_status(am):
    if not am:
        return False
    for r1 in am:
        if not r1.status:
            return False
    return True        

def check_system_mac(mac):
    for r1 in all_switches:
        if mac == r1.system_mac:
            return r1.hostname
    else:
        return None

def query_switch(switch_con,new_mac_search):
    response_current_switch = switch_con.run_commands(['show mac address-table'])
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
                        res_check = check_all_macs(r1['macAddress'])
                        if res_check:
                            if not res_check.status:
                                res_check.switch = switch_con.hostname
                                res_check.interface = intf_members
                                if r1['vlanId'] not in res_check.vlan:
                                    res_check.vlan.append(r1['vlanId'])
                            switch_con.add_mac(res_check)
                        else:
                            current_mac = MACHOSTS(r1['macAddress'],[r1['vlanId']],switch_con.hostname,intf_members)
                            all_macs.append(current_mac)
                            switch_con.add_mac(current_mac)
                else:
                    res_check = check_all_macs(r1['macAddress'])
                    if res_check:
                        if not res_check.status:
                            res_check.switch = switch_con.hostname
                            res_check.interface = [r1['interface']]
                            if r1['vlanId'] not in res_check.vlan:
                                res_check.vlan.append(r1['vlanId'])
                        switch_con.add_mac(res_check)
                    else:
                        current_mac = MACHOSTS(r1['macAddress'],[r1['vlanId']],switch_con.hostname,[r1['interface']])
                        all_macs.append(current_mac)
                        switch_con.add_mac(current_mac)

def search_results(switch_object):
    "Function to take the search results and evaluate the data"
    if switch_object.mac_entry:
        for r1 in switch_object.mac_entry:
            if r1.status:
                continue
            check_system = check_system_mac(r1.mac)
            if check_system:
                r1.status = True
                r1.switch = check_system
                r1.interface = 'SYSTEM MAC'
            else:
                for r2 in r1.interface:
                    if r2 not in switch_object.lldp_neighbors:
                        r1.status = True
                        r1.switch = switch_object.hostname
                        r1.interface = r2
                    elif r2 in switch_object.lldp_neighbors:
                        remote_ip = switch_object.lldp_neighbors[r2]['ip']
                        if remote_ip not in checked_switches and remote_ip not in search_devices:
                            search_devices.append({switch_object.lldp_neighbors[r2]['ip']:switch_object.lldp_neighbors[r2]['Arista']})
                    else:
                        for r3 in switch_object.lldp_neighbors:
                            remote_ip = switch_object.lldp_neighbors[r3]['ip']
                            if remote_ip not in checked_switches and remote_ip not in search_devices:
                                search_devices.append({remote_ip:switch_object.lldp_neighbors[r2]['Arista']})
    #else:
    for r1 in switch_object.lldp_neighbors:
        remote_ip = switch_object.lldp_neighbors[r1]['ip']
        if remote_ip not in checked_switches and remote_ip not in search_devices:
            search_devices.append({remote_ip:switch_object.lldp_neighbors[r1]['Arista']})
    for r1 in all_macs:
        if not r1.status:
            check_system = check_system_mac(r1.mac)
            if check_system:
                r1.status = True
                r1.switch = check_system
                r1.interface = 'SYSTEM MAC'
            
        

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
    current_switch = SwitchCon('localhost',switch_username,switch_password,s_vend=True)
    all_switches.append(current_switch)
    query_switch(current_switch,new_mac_search)
    #Iterate through mac entries found
    search_results(current_switch)
    if not check_all_mac_status(all_macs):
        for r1 in search_devices:
            rem_ip = r1.keys()[0]
            if rem_ip not in checked_switches:
                checked_switches.append(r1.keys()[0])
                rem_ven = r1[rem_ip]
                remote_switch = SwitchCon(rem_ip,switch_username,switch_password,s_vend=rem_ven)
                all_switches.append(remote_switch)
                query_switch(remote_switch,new_mac_search)
                search_results(remote_switch)
    print_output(all_macs)

#==========================================
# End Main Function
#==========================================

if __name__ == '__main__':
    if len(argv) > 1:
        main(argv[1])
    else:
        print('MAC Address not provided')
