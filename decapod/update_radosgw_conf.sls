{% set monitors = {} %}
{%- for node_name, node_grains in salt['mine.get']('ceph-mon*', 'grains.items').iteritems() %}
  {%- set localhost = node_grains.get('localhost', {}) %}
  {%- set ip = node_grains.get('ip_interfaces', {}).get('ens3', {})[0] %}
  {% do monitors.update({localhost : ip}) %}
{%- endfor %}

update radosgw configuration:
  file.blockreplace:
    - name: /etc/ceph/ceph.conf
    - marker_start: "[client.rgw.ceph-mon01]"
    - marker_end: "[client.restapi]"
    - content: |
        {%- for mon,ip in monitors.iteritems() | sort() %}
          {%- if mon != 'ceph-mon01' %}
          [client.rgw.{{ mon }}]
          {%- endif %}
          host = {{ mon }}
          keyring = /var/lib/ceph/radosgw/ceph-rgw.{{ mon }}/keyring
          rgw socket path = /tmp/radosgw-{{ mon }}.sock
          log file = /var/log/ceph/ceph-rgw-{{ mon }}.log
          rgw data = /var/lib/ceph/radosgw/ceph-rgw.{{ mon }}
          rgw frontends = civetweb port={{ ip }}:8080 num_threads=50

          rgw content length compat = True
          rgw dns name = ${_param:cluster_domain}
          rgw keystone accepted roles = _member_, Member, admin, swiftoperator
          rgw keystone admin_token = ${_param:keystone_service_token}
          rgw keystone revocation interval = 60
          rgw keystone url = ${_param:keystone_service_host}:5000
          rgw print_continue = True
          rgw s3 auth use keystone = True
        {% endfor %}

    - append_if_not_found: True
    - backup: '.bak'
    - show_changes: True

radosgw:
  service.running:
    - enable: True

