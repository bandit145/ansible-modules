#!/usr/bin/python
# Copyright: (c) 2019, Philip Bove <phil@bove.online>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
'''

EXAMPLES = '''
'''

RETURN = '''
'''

DNS_RECORDS_SPEC = dict(
	host=dict(type='str', required=True),
	ttl=dict(type='int', required=False, default=None),
	data=dict(type='list', required=True),
	type=dict(type='str',required=True),
)

IN_LIST = [
	'a',
	'aaa',
	'apl',
	'dhcid',
	'ipseckey',
	'kx',
	'naptr',
	'nsap',
	'nsap_ptr',
	'px',
	'srv',
	'wks'
]

ANY_LIST = [
	'afsdb',
	'avc',
	'caa',
	'cdnskey',
	'cds',
	'cert',
	'cname',
	'csync',
	'dlv',
	'dname',
	'dnskey',
	'ds',
	'eui48',
	'eui64',
	'gpos',
	'hinfo',
	'hip',
	'isdn',
	'loc',
	'mx',
	'ns',
	'nsec',
	'nsec3',
	'nsec3param',
	'openpgpkey',
	'ptr',
	'rp',
	'rrsig',
	'rt',
	'spf',
	'sshfp',
	'tlsa',
	'txt',
	'uri',
	'x25'
]

from ansible.module_utils.basic import AnsibleModule
import importlib
import os

try:
	import dns.zone
	import dns.rdatatype
	import dns.rdtypes.IN as IN
	import dns.rdtypes.ANY as ANY
	DNS_INSTALLED = True
except ImportError:
	DNS_INSTALLED = False


def find_zone(module):
	if os.path.exists:
		return True, dns.zone.Zone.from_file(module.params['zone_path']+'db.'+module.params['name'])
	return False, None


def build_zone(module, serial):
	zone = dns.zone.Zone(module.params['origin'])
	# create soa seperate
	if not serial:
		serial = 0
	soa_rdataset = zone.find_rdataset(module.params['name'], dns.rdataclass.ANY, dns.rdatatype.SOA, create=True)
	soa_rdata = ANY.SOA.SOA(dns.rdataclass.ANY, dns.rdatatype.SOA, module.params['expire'], module.params['minimum'], module.params['master_name'], 
		module.params['refresh'], module.params['retry'], module.params['responsible_name'], serial)
	soa_rdataset.add(soa_rdata, module.params['ttl'])

	for host in module.params['records']:
		if host['ttl']:
			ttl = host['ttl']
		else:
			ttl = module.param['ttl']
		rdataset = zone.find_rdataset(host['host'], create=True)
		if host.type.lower() in ANY_LIST:
			rdata = getattr(ANY, host.type.upper())(dns.rdataclass.ANY, getattr(dns.rdatatype, host.type.upper()), **host['data'])
		elif host.type.lower() in IN_LIST:
			rdata = getattr(IN, host.type.upper())(dns.rdataclass.IN, getattr(dns.rdatatype, host.type.upper()), **host['data'])
		else:
			module.fail_json(msg='record type not supported')
		rdataset.add(rdata, ttl)
	return zone


def update_dyn_zone(module, zone):
	soa_rdataset = zone.find_rdataset(module.params['name'], dns.rdataclass.ANY, dns.rdatatype.SOA)
	soa_rdata = soa.rdataset.items[0].copy()
	for host in module.params['records']:
		rdataset = zone.get_rdataset(host['host'], create=True)
		for  record in  rdataset.items:
		if rdataset:
			if host.type.lower() in ANY_LIST:
				rdata = getattr(ANY, host.type.upper())(dns.rdataclass.ANY, getattr(dns.rdatatype, host.type.upper()), **host['data'])
			elif host.type.lower() in IN_LIST:
				rdata = getattr(IN, host.type.upper())(dns.rdataclass.IN, getattr(dns.rdatatype, host.type.upper()), **host['data'])
			else:
				module.fail_json(msg='record type not supported')
			rdataset.add(rdata, ttl)


def ensure(module, hosts):
	pass


def main():
	module = AnsibleModule(
			argument_spec=dict(
				ttl=dict(type='int', required=True),
				origin=dict(type='str', required=False),
				master_name=dict(type='str', required=True),
				records=dict(type='list', required=True),
				responsible_name=dict(type='str', required=True),
				refresh=dict(type='int', required=False, default=3),
				retry=dict(type='int', required=False, default=1),
				expire=dict(type='int', required=False, default=1),
				negative_caching=dict(type='str', required=False, default='1h'),
				dynamic=dict(type='bool', required=False, choices=[True, False]),
				records=dict(type='list', required=True, elements='dict', options=DNS_RECORDS_SPEC),
				state=dict(type='str', required=True, default='present', choices=['present','absent']),
				zone_path=dict(type='path', required=True, default='/var/named/')
			),
			supports_check_mode=True
	)
	if not DNS_INSTALLED:
		module.fail_json(msg='dnspython not installed')
	hosts = []
	for record in module.params['records']:
		hosts.append(record['host'])
	ensure(module, hosts)

if __name__ == '__main__':
	main()