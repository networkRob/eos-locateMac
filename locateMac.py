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
from pprint import pprint as pp

dict_nodes = {}
dict_all_mac_matches = {}

switch_username = 'arista'
switch_password = 'arista'
checked_switches = []

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
    print('MAC Address\t\tHostname\tInterface')
    print('%s\t%s\t\t%s'%(data))

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
    

#==========================================
# End Function Declarations
#==========================================
# Begin Main Function
#==========================================


def main(mac_to_search):
    "Main script to get started"
    #Status Variable
    SEARCH_STATUS = False
    search_count = 0 #counting variable to prevent forever loop
    search_devices = [] # List containing IPs to remote query
    #Reformat MAC search string
    if '.' in mac_to_search:
        new_mac_search = format_MAC(mac_to_search)
    elif ':' in mac_to_search:
        new_mac_search = mac_to_search
    else:
        new_mac_search = format_MAC(mac_to_search)
    current_switch = SwitchCon('localhost',switch_username,switch_password)
    query_switch(current_switch,new_mac_search)
    #Iterate through mac entries found
    for r1 in current_switch.mac_entry:
        for r2 in current_switch.mac_entry[r1]['interface']:
            #Evaluate if the interface the MAC was found on has a LLDP neighbor entry
            if r2 not in current_switch.lldp_neighbors: 
                SEARCH_STATUS = True
                mac_switch_result = (current_switch.hostname,r2,r1)
            else:
                for r3 in current_switch.lldp_neighbors:
                    search_devices.append(current_switch.lldp_neighbors[r3]['ip'])
    while not SEARCH_STATUS:
        if search_count >= 20:
            print('Not found')
            break
        search_count += 1
        for r1 in search_devices:
            if r1 not in checked_switches:
                checked_switches.append(r1)
                remote_switch = SwitchCon(r1,switch_username,switch_password)
                query_switch(remote_switch,new_mac_search)
                for r2 in remote_switch.mac_entry:
                    for r3 in remote_switch.mac_entry[r2]['interface']:
                        #Evaluate if the interface the MAC was found on has a LLDP neighbor entry
                        if r3 not in remote_switch.lldp_neighbors: 
                            SEARCH_STATUS = True
                            mac_switch_result = (remote_switch.hostname,r3,r2)
                        else:
                            for r4 in remote_switch.lldp_neighbors:
                                if remote_switch.lldp_neighbors[r4]['ip'] not in checked_switches and remote_switch.lldp_neighbors[r4]['ip'] not in search_devices:
                                    search_devices.append(remote_switch.lldp_neighbors[r4]['ip'])
    if SEARCH_STATUS:
        print_output(mac_switch_result)
                    

                        
                
    #TODO: Check to see if a match was found on local switch end and report
    #TODO: If match found on remote switch, query remote switch, if round end and report it.  If on remote, repeat queries

#==========================================
# End Main Function
#==========================================

if __name__ == '__main__':
    if len(argv) > 1:
        main(argv[1])
    else:
        print('MAC Address not provided')
