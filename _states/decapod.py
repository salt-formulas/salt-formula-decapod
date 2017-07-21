def __virtual__():
    return 'decapod'


def cluster_present(name):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': '',
           }

    cluster = __salt__['decapod.get_cluster'](name)

    if cluster:
        ret['result'] = True
        ret['comment'] = "Cluster {0} present".format(name)
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'decapod.cluster_present would ' \
            'create an cluster {0}'.format(name)
        return ret

    new_cluster = __salt__['decapod.create_cluster'](name)

    ret['comment'] = "Created cluster '{0}'".format(name)
    ret['changes'] = {
        'old': None,
        'new': new_cluster['id'],
    }
    ret['result'] = True

    return ret


def cluster_absent(name):
    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': '',
           }

    cluster = __salt__['decapod.get_cluster'](name)

    if not cluster:
        ret['result'] = True
        ret['comment'] = "Cluster {0} present".format(name)
        return ret

    if __opts__['test']:
        ret['result'] = None
        ret['comment'] = 'decapod.cluster_present would ' \
            'delete an cluster {0}'.format(name)
        return ret

    __salt__['decapod.delete_cluster'](name)

    ret['comment'] = "Deleted cluster '{0}'".format(name)
    ret['changes'] = {
        'old': cluster['id'],
        'new': None,
    }
    ret['result'] = True

    return ret


def playbook_configuration_present(name, cluster_name='ceph', cfg_type=None,
                                   hints=[], osds={}, mons={}, rgws={},
                                   raw_config={}):

    def _deep_merge(dct, merge_dct):
        for k, v in merge_dct.iteritems():
            if (k in dct and isinstance(dct[k], dict)):
                _deep_merge(dct[k], merge_dct[k])
            else:
                dct[k] = merge_dct[k]

    ret = {'name': name,
           'changes': {},
           'result': True,
           'comment': '',
           }
    pb_cfg = __salt__['decapod.get_playbook_configuration'](name)

    if not pb_cfg:
        if __opts__['test']:
            ret['result'] = None
            msg = "Configuration {0} for cluser {1} will be created"
            ret['comment'] = msg.format(name, cluster_name)
            return ret

        all_servers = __salt__['decapod.get_servers']()

        servers = []
        for srv in all_servers:
            ip = srv.get('data', {}).get('ip', '')
            if ip in set(osds.keys() + mons.keys() + rgws.keys()):
                servers.append(srv['id'])

        try:
            base_cfg = __salt__['decapod.create_playbook_configuration'](
                name,
                cluster_name,
                cfg_type,
                hints=hints,
                nodes=servers
            )

            configuration = base_cfg.get('data', {}).get('configuration', {})
            inv = configuration.get('inventory', {})

            if osds != {}:
                _deep_merge(inv['_meta']['hostvars'], osds)
                inv['osds'] = osds.keys()
            if mons != {}:
                _deep_merge(inv['_meta']['hostvars'], mons)
                inv['mons'] = mons.keys()
            if rgws != {}:
                _deep_merge(inv['_meta']['hostvars'], rgws)
                inv['rgws'] = rgws.keys()

            _deep_merge(configuration, raw_config)

            new_cfg = __salt__['decapod.update_playbook_configuration'](
                name,
                cluster_name,
                configuration
            )
        except:
            __salt__['decapod.delete_playbook_configuration'](name,
                                                              cluster_name)
            raise

        msg = "Created configuration '{0}' for cluster {1}"
        ret['comment'] = msg.format(name, cluster_name)
        ret['changes'] = {
            'old': None,
            'new': new_cfg
        }
        ret['result'] = True
        return ret

    ret['result'] = True
    ret['comment'] = "Configuration {0} present and uptodate".format(name)
    return ret
