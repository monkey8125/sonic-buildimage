import json
import os
import subprocess

import tests.common_utils as utils
import minigraph

from unittest import TestCase

TOR_ROUTER = 'ToRRouter'
BACKEND_TOR_ROUTER = 'BackEndToRRouter'
BMC_MGMT_TOR_ROUTER = 'BmcMgmtToRRouter'

class TestCfgGenCaseInsensitive(TestCase):

    def setUp(self):
        self.test_dir = os.path.dirname(os.path.realpath(__file__))
        self.script_file = utils.PYTHON_INTERPRETTER + ' ' + os.path.join(self.test_dir, '..', 'sonic-cfggen')
        self.sample_graph = os.path.join(self.test_dir, 'simple-sample-graph-case.xml')
        self.sample_simple_graph = os.path.join(self.test_dir, 'simple-sample-graph.xml')
        self.sample_resource_graph = os.path.join(self.test_dir, 'sample-graph-resource-type.xml')
        self.sample_subintf_graph = os.path.join(self.test_dir, 'sample-graph-subintf.xml')
        self.port_config = os.path.join(self.test_dir, 't0-sample-port-config.ini')

    def run_script(self, argument, check_stderr=False):
        print('\n    Running sonic-cfggen ' + argument)
        if check_stderr:
            output = subprocess.check_output(self.script_file + ' ' + argument, stderr=subprocess.STDOUT, shell=True)
        else:
            output = subprocess.check_output(self.script_file + ' ' + argument, shell=True)

        if utils.PY3x:
            output = output.decode()

        linecount = output.strip().count('\n')
        if linecount <= 0:
            print('    Output: ' + output.strip())
        else:
            print('    Output: ({0} lines, {1} bytes)'.format(linecount + 1, len(output)))
        return output

    def test_dummy_run(self):
        argument = ''
        output = self.run_script(argument)
        self.assertEqual(output, '')

    def test_minigraph_sku(self):
        argument = '-v "DEVICE_METADATA[\'localhost\'][\'hwsku\']" -m "' + self.sample_graph + '"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), 'Force10-S6000')

    def test_print_data(self):
        argument = '-m "' + self.sample_graph + '" --print-data'
        output = self.run_script(argument)
        self.assertTrue(len(output.strip()) > 0)

    def test_jinja_expression(self):
        argument = '-m "' + self.sample_graph + '" -v "DEVICE_METADATA[\'localhost\'][\'type\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), 'ToRRouter')

    def test_minigraph_subtype(self):
        argument = '-m "' + self.sample_graph + '" -v "DEVICE_METADATA[\'localhost\'][\'subtype\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), 'DualToR')

    def test_minigraph_peer_switch_hostname(self):
        argument = '-m "' + self.sample_graph + '" -v "DEVICE_METADATA[\'localhost\'][\'peer_switch\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), 'switch2-t0')

    def test_additional_json_data(self):
        argument = '-a \'{"key1":"value1"}\' -v key1'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), 'value1')

    def test_read_yaml(self):
        argument = '-v yml_item -y ' + os.path.join(self.test_dir, 'test.yml')
        output = self.run_script(argument)
        self.assertEqual(output.strip(), '[\'value1\', \'value2\']')

    def test_render_template(self):
        argument = '-y ' + os.path.join(self.test_dir, 'test.yml') + ' -t ' + os.path.join(self.test_dir, 'test.j2')
        output = self.run_script(argument)
        self.assertEqual(output.strip(), 'value1\nvalue2')

#     everflow portion is not used
#     def test_minigraph_everflow(self):
#         argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v MIRROR_SESSION'
#         output = self.run_script(argument)
#         self.assertEqual(output.strip(), "{'everflow0': {'src_ip': '10.1.0.32', 'dst_ip': '10.0.100.1'}}")

    def test_minigraph_interfaces(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v \'INTERFACE.keys()|list\''
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "[('Ethernet0', '10.0.0.58/31'), 'Ethernet0', ('Ethernet0', 'FC00::75/126')]")

    def test_minigraph_vlans(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v VLAN'
        output = self.run_script(argument)

        expected = {
                   'Vlan1000': {
                       'alias': 'ab1',
                       'dhcp_servers': ['192.0.0.1', '192.0.0.2'],
                       'dhcpv6_servers': ['fc02:2000::1', 'fc02:2000::2'],
                       'vlanid': '1000',
                       'mac': '00:aa:bb:cc:dd:ee',
                       },
                   'Vlan2000': {
                       'alias': 'ab2',
                       'dhcp_servers': ['192.0.0.1'],
                       'dhcpv6_servers': ['fc02:2000::3', 'fc02:2000::4'],
                       'vlanid': '2000'
                       }
                   }
        self.assertEqual(
            utils.to_dict(output.strip()),
            expected
        )

    def test_minigraph_vlan_members(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v VLAN_MEMBER'
        output = self.run_script(argument)
        expected = {
                       'Vlan1000|Ethernet8': {'tagging_mode': 'untagged'},
                       'Vlan2000|Ethernet4': {'tagging_mode': 'untagged'}
                   }
        self.assertEqual(
                utils.to_dict(output.strip()),
                expected
        )

    def test_minigraph_vlan_interfaces_keys(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "VLAN_INTERFACE.keys()|list"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "[('Vlan1000', '192.168.0.1/27'), 'Vlan1000']")

    def test_minigraph_vlan_interfaces(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "VLAN_INTERFACE"'
        output = self.run_script(argument)
        expected_table = {
            'Vlan1000|192.168.0.1/27': {},
            'Vlan1000': {
                'proxy_arp': 'enabled',
                'grat_arp': 'enabled'
            }
        }
        self.assertEqual(utils.to_dict(output.strip()), expected_table)

    def test_minigraph_portchannels(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v PORTCHANNEL'
        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            utils.to_dict("{'PortChannel01': {'admin_status': 'up', 'min_links': '1', 'members': ['Ethernet4'], 'mtu': '9100', 'tpid': '0x8100'}}")
        )

    def test_minigraph_console_mgmt_feature(self):
        argument = '-m "' + self.sample_graph + '" -v CONSOLE_SWITCH'
        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            utils.to_dict("{'console_mgmt': {'enabled': 'no'}}"))

    def test_minigraph_console_port(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v CONSOLE_PORT'
        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            utils.to_dict("{'1': {'baud_rate': '9600', 'remote_device': 'managed_device', 'flow_control': 1}}"))

    def test_minigraph_dhcp_server_feature(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "DEVICE_METADATA[\'localhost\'][\'dhcp_server\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), '')

        try:
            # For DHCP server enabled device type
            output = subprocess.check_output("sed -i \'s/%s/%s/g\' %s" % (TOR_ROUTER, BMC_MGMT_TOR_ROUTER, self.sample_graph), shell=True)
            output = self.run_script(argument)
            self.assertEqual(output.strip(), 'enabled')
        finally:
            output = subprocess.check_output("sed -i \'s/%s/%s/g\' %s" % (BMC_MGMT_TOR_ROUTER, TOR_ROUTER, self.sample_graph), shell=True)

    def test_minigraph_deployment_id(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "DEVICE_METADATA[\'localhost\'][\'deployment_id\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "1")

    def test_minigraph_cluster(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "DEVICE_METADATA[\'localhost\'][\'cluster\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "AAA00PrdStr00")

    def test_minigraph_neighbor_metadata(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "DEVICE_NEIGHBOR_METADATA"'

        expected_table = {
            'switch-01t1': { 
                'lo_addr': '10.1.0.186/32',
                'mgmt_addr': '10.7.0.196/26',
                'hwsku': 'Force10-S6000',
                'type': 'LeafRouter',
                'deployment_id': '2'
            },
            'switch2-t0': {
                'hwsku': 'Force10-S6000',
                'lo_addr': '25.1.1.10/32',
                'mgmt_addr': '10.7.0.196/26',
                'type': 'ToRRouter'
            },
            'server1': {
                'hwsku': 'server-sku',
                'lo_addr': '10.10.10.1/32',
                'lo_addr_v6': 'fe80::0001/80',
                'mgmt_addr': '10.0.0.1/32',
                'type': 'Server'
            },
            'server2': {
                'hwsku': 'server-sku',
                'lo_addr': '10.10.10.2/32',
                'lo_addr_v6': 'fe80::0002/128',
                'mgmt_addr': '10.0.0.2/32',
                'type': 'Server'
            }
        }
        output = self.run_script(argument)
        self.maxDiff = None
        self.assertEqual(
            utils.to_dict(output.strip()),
            expected_table
        )

#     everflow portion is not used
#     def test_metadata_everflow(self):
#         argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "MIRROR_SESSION"'
#         output = self.run_script(argument)
#         self.assertEqual(output.strip(), "{'everflow0': {'src_ip': '10.1.0.32', 'dst_ip': '10.0.100.1'}}")

    def test_metadata_tacacs(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "TACPLUS_SERVER"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "{'10.0.10.7': {'priority': '1', 'tcp_port': '49'}, '10.0.10.8': {'priority': '1', 'tcp_port': '49'}}")

    def test_metadata_kube(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "KUBERNETES_MASTER[\'SERVER\']"'
        output = self.run_script(argument)
        self.assertEqual(json.loads(output.strip().replace("'", "\"")),
                json.loads('{"ip": "10.10.10.10", "disable": "True"}'))

    def test_minigraph_mgmt_port(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "MGMT_PORT"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "{'eth0': {'alias': 'eth0', 'admin_status': 'up', 'speed': '1000'}}")

    def test_metadata_ntp(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "NTP_SERVER"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "{'10.0.10.1': {}, '10.0.10.2': {}}")

    def test_minigraph_vnet(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "VNET"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "")

    def test_minigraph_vxlan(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "VXLAN_TUNNEL"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "")

    def test_minigraph_bgp_mon(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "BGP_MONITORS"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "{}")

    def test_minigraph_peer_switch(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "PEER_SWITCH"'
        expected_table = {
            'switch2-t0': {
                'address_ipv4': "25.1.1.10"
            }
        }
        
        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            expected_table
        )

    def test_mux_cable_parsing(self):
        result = minigraph.parse_xml(self.sample_graph, port_config_file=self.port_config)
        
        expected_mux_cable_ports = ["Ethernet4", "Ethernet8"]
        port_table = result['PORT']
        for port_name, port in port_table.items():
            if port_name in expected_mux_cable_ports:
                self.assertTrue(port["mux_cable"])
            else:
                self.assertTrue("mux_cable" not in port)

    def test_minigraph_storage_device(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "DEVICE_METADATA[\'localhost\'][\'storage_device\']"'
        output = self.run_script(argument)
        self.assertEqual(output.strip(), "true")

    def test_minigraph_storage_backend_no_resource_type(self):
        self.verify_storage_device_set(self.sample_simple_graph)

    def test_minigraph_storage_backend_resource_type(self):
        self.verify_storage_device_set(self.sample_resource_graph)

    def test_minigraph_storage_backend_subintf(self):
        self.verify_storage_device_set(self.sample_subintf_graph)

    def verify_storage_device_set(self, graph_file, check_stderr=False):
        try:
            print('\n    Change device type to %s' % (BACKEND_TOR_ROUTER))
            if check_stderr:
                output = subprocess.check_output("sed -i \'s/%s/%s/g\' %s" % (TOR_ROUTER, BACKEND_TOR_ROUTER, graph_file), stderr=subprocess.STDOUT, shell=True)
            else:
                output = subprocess.check_output("sed -i \'s/%s/%s/g\' %s" % (TOR_ROUTER, BACKEND_TOR_ROUTER, graph_file), shell=True)

            argument = '-m "' + graph_file + '" -p "' + self.port_config + '" -v "DEVICE_METADATA[\'localhost\'][\'storage_device\']"'
            output = self.run_script(argument)
            self.assertEqual(output.strip(), "true")

        finally:
            print('\n    Change device type back to %s' % (TOR_ROUTER))
            if check_stderr:
                output = subprocess.check_output("sed -i \'s/%s/%s/g\' %s" % (BACKEND_TOR_ROUTER, TOR_ROUTER, graph_file), stderr=subprocess.STDOUT, shell=True)
            else:
                output = subprocess.check_output("sed -i \'s/%s/%s/g\' %s" % (BACKEND_TOR_ROUTER, TOR_ROUTER, graph_file), shell=True)
  
    def test_minigraph_tunnel_table(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "TUNNEL"'
        expected_tunnel = {
            "MuxTunnel0": {
                "tunnel_type": "IPINIP",
                "dst_ip": "10.1.0.32",
                "dscp_mode": "uniform",
                "encap_ecn_mode": "standard",
                "ecn_mode": "copy_from_outer",
                "ttl_mode": "pipe"
            }
        }

        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            expected_tunnel
        )

    def test_minigraph_mux_cable_table(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "MUX_CABLE"'
        expected_table = {
            'Ethernet4': {
                'state': 'auto',
                'server_ipv4': '10.10.10.1/32',
                'server_ipv6': 'fe80::1/128'
            },
            'Ethernet8': {
                'state': 'auto',
                'server_ipv4': '10.10.10.2/32',
                'server_ipv6': 'fe80::2/128'
            }
        }

        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            expected_table
        )
    
    def test_dhcp_table(self):
        argument = '-m "' + self.sample_graph + '" -p "' + self.port_config + '" -v "DHCP_RELAY"'
        expected = {
                   'Vlan1000': {
                       'dhcpv6_servers': [
                           "fc02:2000::1",
                           "fc02:2000::2"
                       ]
                    },
                    'Vlan2000': {
                       'dhcpv6_servers': [
                           "fc02:2000::3",
                           "fc02:2000::4"
                       ]
                    }
        }
        output = self.run_script(argument)
        self.assertEqual(
            utils.to_dict(output.strip()),
            expected
        )
    
    def test_minigraph_mirror_dscp(self):
        result = minigraph.parse_xml(self.sample_graph, port_config_file=self.port_config)
        self.assertTrue('EVERFLOW_DSCP' in result['ACL_TABLE'])
        everflow_dscp_entry = result['ACL_TABLE']['EVERFLOW_DSCP']
        
        self.assertEqual(everflow_dscp_entry['type'], 'MIRROR_DSCP')
        self.assertEqual(everflow_dscp_entry['stage'], 'ingress')
        expected_ports = ['PortChannel01', 'Ethernet12', 'Ethernet8', 'Ethernet0']
        self.assertEqual(
            everflow_dscp_entry['ports'].sort(),
            expected_ports.sort()
        )


    
