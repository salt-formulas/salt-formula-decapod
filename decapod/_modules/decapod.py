'''
decapod module
'''
import salt.utils

import oauth.oauth as oauth
import httplib2
import uuid

import re
import json

import os

import base64

import decapodlib

import logging
log = logging.getLogger(__name__)

__func_alias__ = {
    'list_': 'list'
}

__virtualname__ = 'decapod'


def __virtual__():
    return __virtualname__


def extractIP(ipStr):
    l = re.split('(.*)\.(.*)\.(.*)\.(.*)/(.*)', ipStr)
    return l[1] + '.' + l[2] + '.' + l[3]


def perform_API_request(site, uri, method, key, secret, consumer_key):
    resource_tok_string = "oauth_token_secret=%s&oauth_token=%s" % (
        secret, key)
    resource_token = oauth.OAuthToken.from_string(resource_tok_string)
    consumer_token = oauth.OAuthConsumer(consumer_key, "")

    oauth_request = oauth.OAuthRequest.from_consumer_and_token(
        consumer_token, token=resource_token, http_url=site,
        parameters={'oauth_nonce': uuid.uuid4().hex})
    oauth_request.sign_request(
        oauth.OAuthSignatureMethod_PLAINTEXT(), consumer_token,
        resource_token)
    headers = oauth_request.to_header()
    url = "%s%s" % (site, uri)
    http = httplib2.Http()
    return http.request(url, method, body=None, headers=headers)


def deploy_nodes(api_key, maas_server, server_discovery_key, decapod_ip, ansible_public_key):
    nodes = []
    api_key = api_key.split(':')
    # API key = '<consumer_key>:<key>:<secret>'
    key = api_key[1]
    secret = api_key[2]
    consumer_key = api_key[0]

    response = perform_API_request(maas_server, '/nodes/', 'GET', key, secret, consumer_key)

    output = response[1].strip(' \t\n\r')
    output_json = json.loads(output)

    for record in output_json:
        match = re.search('ceph-mon0[0-3]|ceph0[1-9]', record['hostname'])
        if match:
            match = re.search('Allocated', record['status_name'])
            if match:
                nodes.append(record['system_id'])

    user_data = """
    #cloud-config
    packages: [python]
    runcmd:
    - [echo, === START DECAPOD SERVER DISCOVERY ===]
    - [sh, -xc, 'grep -q ''/usr/share/server_discovery.sh'' /etc/rc.local || sed -i ''s?^exit 0?/usr/share/server_discovery.sh >> /var/log/server_discovery.log 2>\&1\nexit 0?'' /etc/rc.local']
    - [sh, -xc, systemctl enable rc-local.service || true]
    - [sh, -xc, /usr/share/server_discovery.sh 2>&1 | tee -a /var/log/server_discovery.log]
    - [echo, === FINISH DECAPOD SERVER DISCOVERY ===]
    users:
    - groups: [sudo]
      name: ansible
      shell: /bin/bash
      ssh-authorized-keys: [""" + ansible_public_key + """]
      sudo: ['ALL=(ALL) NOPASSWD:ALL']
    write_files:
    - content: |
        #-*- coding: utf-8 -*-

        from __future__ import print_function

        import json
        import ssl
        import sys

        try:
            import urllib.request as urllib2
        except ImportError:
            import urllib2

        data = {
            "username": u'ansible',
            "host": sys.argv[1].lower().strip(),
            "id": sys.argv[2].lower().strip()
        }
        data = json.dumps(data).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": '""" + server_discovery_key + """',
            "User-Agent": "cloud-init server discovery"
        }

        request = urllib2.Request(u'http://""" + decapod_ip + """:9999/v1/server/', data=data, headers=headers)
        request_kwargs = {"timeout": 5}
        if sys.version_info >= (2, 7, 9):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            request_kwargs["context"] = ctx

        try:
            urllib2.urlopen(request, **request_kwargs).read()
        except Exception as exc:
            sys.exit(str(exc))

        print("Server discovery completed.")
      path: /usr/share/server_discovery.py
      permissions: '0440'
    - content: |
        #!/bin/bash
        set -xe -o pipefail

        echo "Date $(date) | $(date -u) | $(date '+%s')"

        main() {
            local ip="$(get_local_ip)"
            local hostid="$(get_local_hostid)"

            python /usr/share/server_discovery.py "$ip" "$hostid"
        }

        get_local_ip() {
            local remote_ipaddr="$(getent ahostsv4 \"""" + decapod_ip + """\" | head -n 1 | cut -f 1 -d ' ')"

            ip route get "$remote_ipaddr" | head -n 1 | rev | cut -d ' ' -f 2 | rev
        }

        get_local_hostid() {
            dmidecode | grep UUID | rev | cut -d ' ' -f 1 | rev
        }

        main
      path: /usr/share/server_discovery.sh
      permissions: '0550'
    """

    user_data = base64.b64encode(user_data)
    for node in nodes:
        command = "maas mirantis machine deploy " + node + " user_data=" + user_data
        os.system(command)

    while 1:
        nodes = []
        response = perform_API_request(maas_server, '/nodes/', 'GET', key, secret, consumer_key)
        output = response[1].strip(' \t\n\r')
        output_json = json.loads(output)

        for record in output_json:
            match = re.search('ceph-mon[0-9]*|ceph[0-9]*', record['hostname'])
            if match:
                match = re.search('Deploying', record['status_name'])
                if match:
                    nodes.append(record['system_id'])

        if len(nodes) == 0:
            break


def generate_config(phys_mon_interface, vm_mon_interface, osd_devices, osd_journal_devices, mon_ips, osd_ips):
    cluster_config = {'global_vars':
    {
        "ceph_facts_template": "/usr/local/lib/python3.5/dist-packages/decapod_common/facts/ceph_facts_module.py.j2",
        "ceph_stable": "true",
        "ceph_stable_distro_source": "jewel-xenial",
        "ceph_stable_release": "jewel",
        "ceph_stable_repo": "http://eu.mirror.fuel-infra.org/decapod/ceph/jewel-xenial",
        "cluster": "ceph",
        "cluster_network": "",
        "copy_admin_key": "true",
        "dmcrypt_dedicated_journal": "false",
        "dmcrypt_journal_collocation": "false",
        "fsid": "",
        "journal_collocation": "false",
        "journal_size": "",
        "max_open_files": "",
        "nfs_file_gw": "false",
        "nfs_obj_gw": "false",
        "os_tuning_params": [
            {
                "name": "fs.file-max",
                "value": 26234859
            },
            {
                "name": "kernel.pid_max",
                "value": 4194303
            }
        ],
        "public_network": "",
        "raw_multi_journal": "true",
        "restapi_template_local_path": "/usr/local/lib/python3.5/dist-packages/decapod_plugin_playbook_deploy_cluster/ceph-rest-api.service"
      },
      'inventory': {
        '_meta': {
          'hostvars': {
          }
        },
        'clients': [],
        'iscsi_gw': [],
        'mdss': [],
        'mons': [],
        'nfss': [],
        'osds': [],
        'rbd_mirrors': [],
        'restapis': [],
        'rgws': []
      }
    }

    cluster_config['global_vars']['journal_size'] = __pillar__.get('decapod', None)['journal_size']
    cluster_config['global_vars']['max_open_files'] = __pillar__.get('decapod', None)['max_open_files']

    for ip in osd_ips:
        cluster_config['inventory']['_meta']['hostvars'][ip] = {
           'ansible_user': 'ansible',
           'devices': [

           ],
           'monitor_interface': "",
           'raw_journal_devices': [

           ]
        }
        cluster_config['inventory']['_meta']['hostvars'][ip]['devices'] = osd_devices
        cluster_config['inventory']['_meta']['hostvars'][ip]['raw_journal_devices'] = osd_journal_devices
        cluster_config['inventory']['_meta']['hostvars'][ip]['monitor_interface'] = phys_mon_interface
        cluster_config['inventory']['osds'].append(ip)

    for ip in mon_ips:
        cluster_config['inventory']['_meta']['hostvars'][ip] = {
            'ansible_user': 'ansible',
            'devices': [
            ],
            'monitor_interface': "",
            'raw_journal_devices': [
            ]
        }

        cluster_config['inventory']['_meta']['hostvars'][ip]['monitor_interface'] = vm_mon_interface
        cluster_config['inventory']['mons'].append(ip)
        cluster_config['inventory']['restapis'].append(ip)
        cluster_config['inventory']['rgws'].append(ip)

    return cluster_config


def configure_cluster(decapod_ip, decapod_user, decapod_pass, storage_network, frontend_network, management_network):
    decapod_ip = "http://" + decapod_ip + ":9999"
    client = decapodlib.Client(decapod_ip, decapod_user, decapod_pass)
    clusterid = ''
    server_ids = []
    mon_ips = []
    osd_ips = []
    # fsid = ''
    match = 0

    cluster = client.get_clusters()

    for record in cluster['items']:
        search = re.search("ceph",record['data']['name'])
        if search:
            match = 1

    if match == 0:
        cluster = client.create_cluster("ceph")

    for record in cluster['items']:
        if record['data']['name'] == "ceph":
            clusterid = record['id']

    servers = client.get_servers()
    for record in servers['items']:
        server_ids.append(record['id'])
        match = re.search("mon",record['data']['name'])
        ip = extractIP(management_network)
        if match:
            for i in record['data']['facts']['ansible_all_ipv4_addresses']:
                match2 = re.search(ip, i)
                if match2:
                    mon_ips.append(i)
        else:
            for i in record['data']['facts']['ansible_all_ipv4_addresses']:
                match2 = re.search(ip, i)
                if match2:
                    osd_ips.append(i)

    playbook_configs = client.get_playbook_configurations()['items']

    match = 0
    for record in playbook_configs:
        search = re.search("deploy-ceph",record['data']['name'])
        if search:
            match = 1

    if match == 0:
        client.create_playbook_configuration("deploy-ceph", clusterid, "cluster_deploy", server_ids)

    phys_mon_interface = __pillar__.get('decapod', None)['phys_mon_interface']
    vm_mon_interface = __pillar__.get('decapod', None)['vm_mon_interface']
    osd_devices = __pillar__.get('decapod', None)['osd_devices']
    osd_journal_devices = __pillar__.get('decapod', None)['osd_journal_devices']

    playbook_configs = client.get_playbook_configurations()['items']
    fsid = playbook_configs[0]['data']['configuration']['global_vars']['fsid']
    config = generate_config(phys_mon_interface, vm_mon_interface, osd_devices, osd_journal_devices, mon_ips, osd_ips)
    config['global_vars']['fsid'] = fsid
    config['global_vars']['cluster_network'] = storage_network
    config['global_vars']['public_network'] = frontend_network

    if playbook_configs[0]['data']['configuration'] == config:
        return True
    else:
        playbook_configs[0]['data']['configuration'] = config
        client.update_playbook_configuration(playbook_configs[0])
