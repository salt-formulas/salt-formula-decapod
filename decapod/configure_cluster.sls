{% set nodes = salt.saltutil.runner('mine.get',
    tgt='ceph*',
    fun='network.get_hostname',
    tgt_type='glob') -%}

{% set osd_ips = [] %}
{% set mon_ips = [] %}
{% for node in nodes %}
  {% set grains = salt.saltutil.runner('mine.get',tgt=node,fun='grains.items') %}
  {%- if grains[node]['decapod_type'] == 'monitor' %}
    {% set ip = grains[node]['fqdn_ip4'] | first %}
    {%- do mon_ips.append(ip) %}
  {%- endif %}
  {%- if grains[node]['decapod_type'] == 'osd' %}
    {% set ip = grains[node]['fqdn_ip4'] | first %}
    {%- do osd_ips.append(ip) %}
  {%- endif %}
{% endfor %}

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

