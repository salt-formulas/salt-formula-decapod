# -*- coding: utf-8 -*-
'''
Module for handling decapod calls.
'''
import json

from decapod_client import V1Client
from salt.exceptions import CommandExecutionError, SaltInvocationError


def __virtual__():
    return True


def _get_decapod_client():
    params = __salt__['config.get']('decapod')
    return V1Client(params.get('url', ''),
                    params.get('user', ''),
                    params.get('password', ''))


def _do_api_call(client, fname):
    if hasattr(client, fname):
        func = getattr(client, fname)
        return func()
    else:
        raise SaltInvocationError(
            "Decapod client has not attribute {0}".format(fname)
        )


def _get_cluster_by_name(client, name):
    for cluster in client.get_clusters().get('items', []):
        if cluster.get('data', {}).get('name', None) == name:
            return cluster
    return False


def _get_playbook_configuration_by_name(client, name):
    for cfg in client.get_playbook_configurations().get('items', []):
        cfg_data = cfg.get('data', {})
        if cfg_data.get('name', None) == name:
            return cfg
    return False

def _check_cfg_exists(client, name, cluster_id):
    pb_cfg = _get_playbook_configuration_by_name(client, name)
    
    return pb_cfg and pb_cfg.get('data', {}).get('cluster_id') == cluster_id

def _compare_dcts(base_dct, update_dct):
    diff = {}
    # Iterate through input dict
    for key, value in update_dct.iteritems():
        # If do not have key in target dict, adding value
        if key not in base_dct:
            diff[key] = value
            continue

        # If values are the same do nothing
        if base_dct[key] == value:
            continue

        # If target value and input value ar dicst and they are differ
        # from each other do recustion. Otherwise just assign input value
        if isinstance(base_dct[key], dict) and \
                isinstance(value, dict):
            diff[key] = _compare_dcts(base_dct[key], update_dct[key])
        else:
            diff[key] = value

        # Remove empty results of recursion
        if diff[key] == {}:
            diff.pop(key, None) 
    return diff


def _set_hdds(hdd_list, cfg):
    inv = cfg.get('data', {}).get('configuration', {}).get('inventory', {})
    hosts = inv.get('_meta', {}).get('hostvars', {})
    osds = {key: val for key, val in hosts.items()
            if val.get('devices', []) != []}
    for osd in osds:
        osds[osd]['devices'] = hdd_list


def _set_mon_ips(mon_pub_list, raw_pb_cfg):
    update_dict = {}
    inv = raw_pb_cfg.get('data', {}).get('configuration', {}).get('inventory', {})
    hosts = inv.get('_meta', {}).get('hostvars', {})
    mons = {key: val for key, val in hosts.items()
            if val.get('devices', []) == []}
    for mon in mons:
        grain = "ipv4:{0}".format(mon)
        net_ifaces = __salt__['mine.get'](
                grain,
                'network.interfaces',
                expr_form='grain'
        )
        for data in net_ifaces.values():
            for iface_data in data.values():
                for ip in iface_data.get('inet', []):
                    if ip.get('address', None) in mon_pub_list:
                        update_dict[mon] = { "monitor_address": ip['address'] }
                        break
    res = {
        'data': {
            'configuration': {
                'inventory': {
                    '_meta': {
                        'hostvars': update_dict
                    }
                }
            }
        }
    }
    _deep_merge(raw_pb_cfg, res)
    return update_dict


def _deep_merge(dct, merge_dct):
    for k, v in merge_dct.iteritems():
        if (k in dct and isinstance(dct[k], dict)):
            _deep_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


def get_playbooks():
    client = _get_decapod_client()
    return client.get_playbooks().get('itmems', [])


def get_clusters():
    client = _get_decapod_client()
    return client.get_clusters().get('items', [])


def get_cluster(name):
    client = _get_decapod_client()
    return _get_cluster_by_name(client, name)

def get_servers():
    client = _get_decapod_client()
    return client.get_servers().get('items', [])

def create_cluster(name):
    client = _get_decapod_client()
    if _get_cluster_by_name(client, name):
        raise CommandExecutionError("Cluster {0} already exists".format(name))
    else:
        return client.create_cluster(name)


def delete_cluster(name):
    client = _get_decapod_client()
    cluster = _get_cluster_by_name(client, name)
    if not cluster:
        raise CommandExecutionError("Cluster {0} does not exists".format(name))
    else:
        return client.delete_cluster(cluster['id'])


def get_playbook_configurations():
    client = _get_decapod_client()
    return client.get_playbook_configurations().get('items', [])

def get_playbook_configuration(name):
    client = _get_decapod_client()
    return _get_playbook_configuration_by_name(client, name)

def create_playbook_configuration(name, cluster_name, cfg_type, hints=[], nodes=[]):
    client = _get_decapod_client()
    cluster = _get_cluster_by_name(client, cluster_name)

    if not cluster:
        raise CommandExecutionError("Cluster {0} does not exists".format(cluster_name))
    elif _check_cfg_exists(client, name, cluster['id']):
        msg = "Playbook config {0} for cluster {1} exists"
        raise CommandExecutionError(msg.format(name, cluster_name))

    all_nodes = client.get_servers().get('items', [])
    if len(all_nodes) == 0:
        raise CommandExecutionError("No nodes are registered")


    cfg_hints = [{'id': hint, 'value': True} for hint in hints]

    res = client.create_playbook_configuration(
        name,
        cluster['id'],
        cfg_type,
        nodes,
        hints = cfg_hints
    )
    return res


def delete_playbook_configuration(name, cluster_name):
    client = _get_decapod_client()
    cluster = _get_cluster_by_name(client, cluster_name)
    pb_cfg = _get_playbook_configuration_by_name(client, name)

    if not cluster:
        raise CommandExecutionError("Cluster {0} does not exist".format(cluster_name)) 
    elif not _check_cfg_exists(client, name, cluster['id']):
        msg = "Playbook config {0} for cluster {1} not found"
        raise CommandExecutionError(msg.format(name, cluster_name))

    return client.delete_playbook_configuration(pb_cfg['id'])
   

def get_cfg_diff(name, cluster_name, data):
    client = _get_decapod_client()
    cluster = _get_cluster_by_name(client, cluster_name)
    pb_cfg = _get_playbook_configuration_by_name(client, name)
    clean_data = json.loads(json.dumps(data))

    if not cluster:
        raise CommandExecutionError("Cluster {0} does not exist".format(cluster_name)) 
    elif not _check_cfg_exists(client, name, cluster['id']):
        msg = "Playbook config {0} for cluster {1} not found"
        raise CommandExecutionError(msg.format(name, cluster_name))

    return _compare_dcts(pb_cfg.get('data', {}).get('configuration', {}), clean_data)
    

def update_playbook_configuration(cfg_name, cluster_name, data):
    client = _get_decapod_client()
    cluster = _get_cluster_by_name(client, cluster_name)
    pb_cfg = _get_playbook_configuration_by_name(client, cfg_name)

    if not cluster:
        raise CommandExecutionError("Cluster {0} does not exist".format(cluster_name)) 
    elif not _check_cfg_exists(client, cfg_name, cluster['id']):
        msg = "Playbook config {0} for cluster {1} not found"
        raise CommandExecutionError(msg.format(cfg_name, cluster_name))

    cfg = pb_cfg.get('data', {}).get('configuration', {})
    _deep_merge(cfg, data)
    return client.update_playbook_configuration(pb_cfg)
