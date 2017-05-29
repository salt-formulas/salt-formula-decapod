{% set osd_ips = [] %}
{% set mon_ips = [] %}
{%- for node_name, node_grains in salt['mine.get']('ceph*', 'grains.items').iteritems() %}
  {%- if node_grains['decapod_type'] == 'monitor' %}
    {%- if node_grains['fqdn'] in pillar['decapod_lcm']['del_mon'] %}
      {%- do mon_ips.append(node_grains['decapod_mgmt_ip']) %}
    {%- endif %}
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
    - mon_ips: {{ mon_ips }}
    - osd_ips: {{ osd_ips }}
    - mode: 'remove_mon'

