#!/usr/bin/python
# Copyright: (c) 2019, Philip Bove <phil@bove.online>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from ansible.module_utils.basic import AnsibleModule
import importlib
import os

try:
    import dns.zone
    import dns.rdatatype
    import dns.exception
    import dns.name
    import dns.rdtypes.IN as IN
    import dns.rdtypes.ANY as ANY
    # this is needed first and as such is explicitly imported
    import dns.rdtypes.ANY.SOA
    DNS_INSTALLED = True
except ImportError:
    DNS_INSTALLED = False


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

DNS_RECORDS_SPEC = dict(
    host=dict(type='str', required=True),
    ttl=dict(type='int', required=False, default=None),
    data=dict(type='dict', required=True),
    type=dict(type='str',required=True)
)

def import_record_type(module, record, rec_class):
    try:
        importlib.import_module('dns.rdtypes.{rec_class}.{rec}'.format(rec=record['type'].upper(), rec_class=rec_class))
    except ImportError:
        module.fail_json(msg='{rec} type not supported in this version of dnspython'.format())


def find_zone(module):
    try:
        zone_path = '{zone_path}/db.{zone_name}'.format(zone_path=module.params['zone_path'], zone_name=module.params['name'])
        if os.path.exists(zone_path):
            return True, dns.zone.from_file(zone_path)
        return False, None
    except dns.exception.DNSException:
        module.fail_json(msg='{zone} zone file syntax incorrect on host'.format(zone=module.params['name']))


def build_zone(module, serial):
    zone = dns.zone.Zone(module.params['name'])
    # create soa seperate
    if not serial:
        serial = 0
    soa_dataset = zone.find_rdataset(dns.name.from_text(module.params['name']), dns.rdatatype.SOA, create=True)
    soa_rdata = dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, module.params['master_name'], module.params['responsible_name'],
        serial, module.params['refresh'], module.params['retry'], module.params['expire'], module.params['negative_caching'])
    soa_rdataset.add(soa_rdata, module.params['ttl'])

    for host in module.params['records']:
        if host['type'].lower() in ANY_LIST:
            rec_class = 'ANY'
        elif host['type'].lower() in IN_LIST:
            rec_class = 'IN'
        else:
            module.fail_json(msg='record type not supported')
        import_record_type(module, host, rec_class)
        if host['ttl']:
            ttl = host['ttl']
        else:
            ttl = module.params['ttl']
        rdataset = zone.find_rdataset(dns.name.from_text(host['host']), getattr(dns.rdatatype, host['type'].upper()), create=True)
        if host['type'].lower() in ANY_LIST:
            rdata = getattr(ANY, host['type'].upper())(dns.rdataclass.IN, getattr(dns.rdatatype, host['type'].upper()), **host['data'])
        elif host['type'].lower() in IN_LIST:
            rdata = getattr(getattr(IN, host['type'].upper()), host['type'].upper())(dns.rdataclass.IN, getattr(dns.rdatatype, host['type'].upper()), **host['data'])
        rdataset.add(rdata, ttl)
    return zone

def ensure(module):
    changed = False
    result, cur_zone = find_zone(module)
    if cur_zone:
        soa_rdata = zone.find_rdataset(module.params['name'], dns.rdataclass.ANY, dns.rdatatype.SOA, create=False)[0]
        serial = soa_rdata.serial
    else:
        serial = None
    new_zone = build_zone(module, serial)
    module.fail_json(msg=new_zone.to_text())
    if module.params['state'] == 'present':
        if new_zone != cur_zone:
            changed = True
            module.fail_json(msg=new_zone.to_text())
            with open('{path}/db.{zone_name}'.format(path=module.params['zone_path'], zone_name=module.params['name']), 'w') as zone_file:
                new_zone.to_file(zone_file)
    elif module.params['state'] == 'absent':
        if cur_zone:
            changed = True
            os.remove('{path}/db.{zone_name}'.format(path=module.params['zone_path'], zone_name=module.params['name']))
    module.exit_json(changed=changed)

def main():
    module = AnsibleModule(
            argument_spec=dict(
                ttl=dict(type='int', required=True),
                name=dict(type='str', required=True, aliases=['origin']),
                master_name=dict(type='str', required=True),
                responsible_name=dict(type='str', required=True),
                refresh=dict(type='int', default=3),
                retry=dict(type='int', default=1),
                expire=dict(type='int',  default=1),
                negative_caching=dict(type='str', default=1),
                dynamic=dict(type='bool', required=False, choices=[True, False]),
                records=dict(type='list', required=True, elements='dict', options=DNS_RECORDS_SPEC),
                state=dict(type='str', default='present', choices=['present','absent']),
                zone_path=dict(type='path', default='/var/named/')
            ),
            supports_check_mode=True
    )
    if not DNS_INSTALLED:
        module.fail_json(msg='dnspython not installed')
    ensure(module)

if __name__ == '__main__':
    main()
