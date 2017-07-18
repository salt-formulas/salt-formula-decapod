import oauth.oauth as oauth
import httplib2
import uuid

import re

import decapodlib

import logging

import time
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


def decapod_api():
    decapod_ip = "http://" + __pillar__.get('decapod', None)['decapod_ip'] + ":9999"
    decapod_user = __pillar__.get('decapod', None)['decapod_user']
    decapod_pass = __pillar__.get('decapod', None)['decapod_pass']
    client = decapodlib.Client(decapod_ip, decapod_user, decapod_pass)
    return client

def add_node(osd_devices, osd_journal_devices, ip, mode):
    client = decapod_api()
    config = {}

    playbook_configs = client.get_playbook_configurations()['items']
    for record in playbook_configs:
        if record['data']['name'] == mode:
            config = record['data']['configuration']['inventory']['_meta']['hostvars'][ip]

    config['devices'] = []
    for i in osd_devices:
        if i not in osd_journal_devices and i not in config['devices']:
            config['devices'].append(i)
    config['raw_journal_devices'] = osd_journal_devices

    for i in range(len(playbook_configs)):
        if playbook_configs[i]['data']['name'] == mode:
            playbook_configs[i]['data']['configuration']['inventory']['_meta']['hostvars'][ip] = config
            client.update_playbook_configuration(playbook_configs[i])

def generate_config(mode, mon_ips, osd_ips, phys_mon_interface='', vm_mon_interface='', add_osd=''):
    if mode == 'cluster_deploy':
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

    if mode == 'add_osd':
        cluster_config = {"global_vars":
        {
            "ceph_facts_template": "/usr/local/lib/python3.5/dist-packages/decapod_common/facts/ceph_facts_module.py.j2",
            "ceph_stable": "true",
            "ceph_stable_distro_source": "jewel-xenial",
            "ceph_stable_release": "jewel",
            "ceph_stable_release_uca": "jewel-xenial",
            "ceph_stable_repo": "http://eu.mirror.fuel-infra.org/decapod/ceph/jewel-xenial",
            "ceph_stable_repo_key": "AF94F6A6A254F5F0",
            "ceph_version_verify": False,
            "ceph_version_verify_packagename": "ceph-common",
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
            "raw_multi_journal": True
        },
        "inventory": {
            "_meta": {
                "hostvars": {

                }
            },
            "already_deployed": [

            ],
            "mons": [

            ],
            "osds": [

            ]
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
            cluster_config['inventory']['already_deployed'].append(ip)

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

        for ip in add_osd:
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

        return cluster_config

    if mode == 'add_mon':
        cluster_config = { "global_vars": {
            "ceph_facts_template": "/usr/local/lib/python3.5/dist-packages/decapod_common/facts/ceph_facts_module.py.j2",
            "ceph_stable": "true",
            "ceph_stable_distro_source": "jewel-xenial",
            "ceph_stable_release": "jewel",
            "ceph_stable_release_uca": "jewel-xenial",
            "ceph_stable_repo": "http://eu.mirror.fuel-infra.org/decapod/ceph/jewel-xenial",
            "ceph_stable_repo_key": "AF94F6A6A254F5F0",
            "ceph_version_verify": False,
            "ceph_version_verify_packagename": "ceph-common",
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
            "raw_multi_journal": True
        },
        "inventory": {
            "_meta": {
                "hostvars": {

                }
            },
            "already_deployed": [
            ],
            "mons": [

            ]
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
            cluster_config['inventory']['already_deployed'].append(ip)

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

        return cluster_config

    if mode == 'remove_mon':
        cluster_config = { "global_vars":
        {
            "cluster": "ceph"
        },
        "inventory": {
            "_meta": {
                "hostvars": {
                }
            },
            "mons": [

            ]
        }
        }

        for ip in mon_ips:
            mon_hostvar = {ip : {"ansible_user": "ansible"}}
            cluster_config['inventory']['_meta']['hostvars'].update(mon_hostvar)
            cluster_config['inventory']['mons'].append(ip)

        return cluster_config

    if mode == 'remove_osd':
        cluster_config = { "global_vars":
        {
            "cluster": "ceph"
        },
        "inventory": {
            "_meta": {
                "hostvars": {

                }
            },
            "mons": [

            ],
            "osds": [

            ]
        }
        }

        for i in mon_ips:
            mon_hostvar = {i : {"ansible_user": "ansible"}}
            cluster_config['inventory']['_meta']['hostvars'].update(mon_hostvar)
            cluster_config['inventory']['mons'].append(i)
        for i in osd_ips:
            osd_hostvar = {i : {"ansible_user": "ansible"}}
            cluster_config['inventory']['_meta']['hostvars'].update(osd_hostvar)
            cluster_config['inventory']['osds'].append(i)

        return cluster_config

    if mode == 'telegraf_integration':
        cluster_config = {
            "global_vars": {
                "ceph_binary": "/usr/bin/ceph",
                "ceph_config": "/etc/ceph/ceph.conf",
                "ceph_user": "client.admin",
                "configpath": "/etc/telegraf/telegraf.conf",
                "gather_admin_socket_stats": True,
                "gather_cluster_stats": True,
                "install": False,
                "interval": "1m",
                "mon_prefix": "ceph-mon",
                "osd_prefix": "ceph-osd",
                "socket_dir": "/var/run/ceph",
                "socket_suffix": "asock",
                "telegraf_agent_collection_jitter": 0,
                "telegraf_agent_deb_url": "https://dl.influxdata.com/telegraf/releases/telegraf_1.1.2_amd64.deb",
                "telegraf_agent_debug": False,
                "telegraf_agent_flush_interval": 10,
                "telegraf_agent_flush_jitter": 0,
                "telegraf_agent_interval": 10,
                "telegraf_agent_logfile": "",
                "telegraf_agent_metric_batch_size": 1000,
                "telegraf_agent_metric_buffer_limit": 10000,
                "telegraf_agent_omit_hostname": False,
                "telegraf_agent_output": [
                    {
                        "config": [
                            "urls = [\"http://localhost:8086\"]",
                            "database = \"telegraf\"",
                            "precision = \"s\""
                        ],
                        "type": "influxdb"
                    }
                ],
                "telegraf_agent_quiet": False,
                "telegraf_agent_round_interval": True,
                "telegraf_agent_tags": {},
                "telegraf_agent_version": "1.1.2",
                "telegraf_plugins_default": [
                    {
                        "config": [
                            "percpu = true"
                        ],
                        "plugin": "cpu"
                    },
                    {
                        "plugin": "disk"
                    },
                    {
                        "plugin": "io"
                    },
                    {
                        "plugin": "mem"
                    },
                    {
                        "plugin": "net"
                    },
                    {
                        "plugin": "system"
                    },
                    {
                        "plugin": "swap"
                    },
                    {
                        "plugin": "netstat"
                    }
                ],
                "telegraf_plugins_extra": {}
            },
            "inventory": {
                "_meta": {
                    "hostvars": {
                    }
                },
                "telegraf": [
                ]
            }
        }

        urls = "urls = [\"" + __pillar__.get('decapod', None)['influxdb_ip'] + "\"]"

        cluster_config['telegraf_agent_output']['config'] = [
            urls,
            "database = \"telegraf\"",
            "precision = \"s\""
        ]

        for ip in mon_ips:
            hostvars = {ip : {"ansible_user": "ansible"}}
            cluster_config['inventory']['_meta']['hostvars'].update(hostvars)
            cluster_config['inventory']['telegraf'].append(ip)
        for ip in osd_ips:
            hostvars = {ip : {"ansible_user": "ansible"}}
            cluster_config['inventory']['_meta']['hostvars'].update(hostvars)
            cluster_config['inventory']['telegraf'].append(ip)

        return cluster_config


def configure_cluster(osd_ips, mon_ips, mode='', add_osd=''):
    client = decapod_api()
    server_ids = []
    match = 0

    cluster = client.get_clusters()

    for record in cluster['items']:
        search = re.search("ceph",record['data']['name'])
        if search:
            match = 1

    if match == 0:
        client.create_cluster("ceph")

    cluster = client.get_clusters()

    for record in cluster['items']:
        if record['data']['name'] == "ceph":
            clusterid = record['id']

    match = 0
    playbook_configs = client.get_playbook_configurations()['items']
    for record in playbook_configs:
        search = re.search(mode,record['data']['name'])
        if search:
            match = 1

    servers = client.get_servers(all_items=True)

    if match == 0:
        if mode == 'remove_mon':
            for record in servers['items']:
                if record['data']['facts']['ansible_fqdn'] in __pillar__.get('decapod_lcm', None)['del_mon']:
                    server_ids.append(record['id'])
        else:
            for record in servers['items']:
                server_ids.append(record['id'])
            client.create_playbook_configuration(mode, clusterid, mode, server_ids)

    phys_mon_interface = __pillar__.get('decapod', None)['phys_mon_interface']
    vm_mon_interface = __pillar__.get('decapod', None)['vm_mon_interface']

    config = generate_config(mode, mon_ips, osd_ips, phys_mon_interface, vm_mon_interface, add_osd)
    if mode != "remove_mon" and mode != "remove_osd" and mode != "telegraf_integration":
        playbook_configs = client.get_playbook_configurations()['items']
        fsid = ''
        for record in playbook_configs:
            search = re.search(mode,record['data']['name'])
            if search:
                fsid = record['data']['configuration']['global_vars']['fsid']

        config['global_vars']['fsid'] = fsid
        config['global_vars']['cluster_network'] = __pillar__.get('decapod', None)['storage_network']
        config['global_vars']['public_network'] = __pillar__.get('decapod', None)['frontend_network']

    for record in playbook_configs:
        search = re.search(mode,record['data']['name'])
        if search:
            if record['data']['configuration'] == config:
                return True
            else:
                record['data']['configuration'] = config
                client.update_playbook_configuration(record)

def execute_configuration(mode):
    client = decapod_api()
    playbook_configs = client.get_playbook_configurations()['items']
    for record in playbook_configs:
        search = re.search(mode,record['data']['name'])
        if search:
            execution = client.create_execution(record["id"], record["version"])
            exec_id = execution["id"]
            while 1:
                execution = client.get_execution(exec_id)
                if execution["data"]["state"] != "started" and execution["data"]["state"] != "created":
                    log.debug(client.get_execution_log(exec_id))
                    break
                else:
                    time.sleep(300)

