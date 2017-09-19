{% set osd_ips = [] %}
{% set mon_ips = [] %}
{% set cache = {} %}

{%- for node_name, node_grains in salt['mine.get']('ceph*', 'grains.items').iteritems() %}
 {%- if node_grains['decapod_type'] == 'monitor' %}
    {%- do mon_ips.append(node_grains['decapod_mgmt_ip']) %}
  {%- endif %}
  {%- if node_grains['decapod_type'] == 'osd' %}
    {%- do osd_ips.append(node_grains['decapod_mgmt_ip']) %}
    {% for device in pillar['decapod']['cache_devices'] %}
      {% if device in node_grains['cache'] %}
        {% do cache.update({node_name: pillar['decapod']['cache_devices']}) %}
      {% else %}
        {% do cache.update({node_name: node_grains['cache']}) %}
        {% break %}
      {% endif %}
    {% endfor %}
  {%- endif %}
{%- endfor %}

configure cluster:
  module.run:
    - name: decapod.configure_cluster
    - storage_network: {{ pillar['decapod']['storage_network'] }}
    - frontend_network: {{ pillar['decapod']['frontend_network'] }}
    - osd_ips: {{ osd_ips }}
    - mon_ips: {{ mon_ips }}
    - mode: "cluster_deploy"

{%- for node_name, node_grains in salt['mine.get']('ceph*', 'grains.items').iteritems() %}
add new node {{ node_name }}:
  module.run:
    - name: decapod.add_node
    {%- if node_grains['pools'] is defined %}
    - osd_devices: {{ node_grains['pools'] | list + pillar['decapod']['ssdpools']| list }}
    {%- else %}
    - osd_devices: ''
    {%- endif %}
    {%- if cache[node_name] is not defined and node_grains['cache'] is not defined %}
    - osd_journal_devices: []
    {%- else %}
    - osd_journal_devices: {{ cache[node_name] | default(node_grains['cache']) }}
    {%- endif %}
    - ip: {{ node_grains['decapod_mgmt_ip'] }}
    - mode: 'cluster_deploy'
{%- endfor %}

#execute configuration:
#  module.run:
#    - name: decapod.execute_configuration
#    - mode: 'cluster_deploy'
