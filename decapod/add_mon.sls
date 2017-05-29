{% set osd_ips = [] %}
{% set mon_ips = [] %}

{%- for node_name, node_grains in salt['mine.get']('ceph*', 'grains.items').iteritems() %}
  {%- if node_grains['decapod_type'] == 'monitor' %}
    {% set ip = node_grains['decapod_mgmt_ip'] %}
    {%- do mon_ips.append(ip) %}
  {%- endif %}
  {%- if node_grains['decapod_type'] == 'osd' %}
    {% set ip = node_grains['decapod_mgmt_ip'] %}
    {%- do osd_ips.append(ip) %}
  {%- endif %}
{%- endfor %}

configure cluster:
  module.run:
    - name: decapod.configure_cluster
    - decapod_ip: {{ pillar['decapod']['decapod_ip'] }}
    - decapod_user: {{ pillar['decapod']['decapod_user'] }}
    - decapod_pass: {{ pillar['decapod']['decapod_pass'] }}
    - storage_network: {{ pillar['decapod']['storage_network'] }}
    - frontend_network: {{ pillar['decapod']['frontend_network'] }}
    - osd_ips: {{ osd_ips }}
    - mon_ips: {{ mon_ips }}
    - mode: 'add_mon'

