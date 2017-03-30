import oauth.oauth as oauth
import httplib2
import uuid

import re

import decapodlib

import logging
log = logging.getLogger(__name__)

__func_alias__ = {
    'list_': 'list'
}

__virtualname__ = 'decapod'


def __virtual__():
    return __virtualname__

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

def add_node(decapod_ip, osd_devices, osd_journal_devices, decapod_user, decapod_pass, ip):
    decapod_ip = "http://" + decapod_ip + ":9999"
    client = decapodlib.Client(decapod_ip, decapod_user, decapod_pass)
    config = {}

    playbook_configs = client.get_playbook_configurations()['items']
    for record in playbook_configs:
        if record['data']['name'] == 'deploy-ceph':
            config = record['data']['configuration']['inventory']['_meta']['hostvars'][ip]

    config['devices'] = []
    for i in osd_devices:
        if i not in osd_journal_devices and i not in config['devices']:
            config['devices'].append(i)
    config['raw_journal_devices'] = osd_journal_devices

    for i in range(len(playbook_configs)):
        if playbook_configs[i]['data']['name'] == 'deploy-ceph':
            playbook_configs[i]['data']['configuration']['inventory']['_meta']['hostvars'][ip] = config
            client.update_playbook_configuration(playbook_configs[i])
            break

def generate_config(phys_mon_interface, vm_mon_interface, mon_ips, osd_ips):
    cluster_config = {'global_vars':
    {
        "ceph_facts_template": "/usr/local/lib/python3.5/dist-packages/decapod_common/facts/ceph_facts_module.py.j2",
        "ceph_stable": "true",
        "ceph_stable_distro_source": "jewel-xenial",
        "ceph_stable_release": "jewel",
        "ceph_stable_repo": "http://eu.mirror.fuel-infra.org/decapod/ceph/jewel-xenial",
        "ceph_stable_repo_key": "AF94F6A6A254F5F0",
        "cluster": "ceph",
        "cluster_network": "",
        "copy_admin_key": True,
        "dmcrypt_dedicated_journal": False,
        "dmcrypt_journal_collocation": False,
        "fsid": "",
        "journal_collocation": False,
        "journal_size": "",
        "max_open_files": "",
        "nfs_file_gw": False,
        "nfs_obj_gw": False,
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
        "raw_multi_journal": True,
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

def configure_cluster(decapod_ip, decapod_user, decapod_pass, storage_network, frontend_network, osd_ips, mon_ips):
    decapod_ip = "http://" + decapod_ip + ":9999"
    client = decapodlib.Client(decapod_ip, decapod_user, decapod_pass)
    clusterid = ''
    server_ids = []
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

    playbook_configs = client.get_playbook_configurations()['items']
    fsid = playbook_configs[0]['data']['configuration']['global_vars']['fsid']
    config = generate_config(phys_mon_interface, vm_mon_interface, mon_ips, osd_ips)
    config['global_vars']['fsid'] = fsid
    config['global_vars']['cluster_network'] = storage_network
    config['global_vars']['public_network'] = frontend_network

    if playbook_configs[0]['data']['configuration'] == config:
        return True
    else:
        playbook_configs[0]['data']['configuration'] = config
        client.update_playbook_configuration(playbook_configs[0])
