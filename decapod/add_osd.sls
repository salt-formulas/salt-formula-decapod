{% set osd_ips = [] %}
{% set mon_ips = [] %}
{% set add_osd = [] %}
{% set cache = {} %}

{%- for node_name, node_grains in salt['mine.get']('ceph*', 'grains.items').iteritems() %}
  {% if node_grains['decapod_type'] == 'monitor' %}
    {%- do mon_ips.append(node_grains['decapod_mgmt_ip']) %}
  {%- endif %}
  {% if node_grains['decapod_type'] == 'osd' %}
    {%- if node_grains['nodename'] not in pillar['decapod_lcm']['add_osd'] %}
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
    {% if node_grains['nodename'] in pillar['decapod_lcm']['add_osds'] %}
      {%- do add_osd.append(node_grains['decapod_mgmt_ip']) %}
      {% for device in pillar['decapod']['cache_devices'] %}
        {% if device in node_grains['cache'] %}
          {% do cache.update({node_name: pillar['decapod']['cache_devices']}) %}
        {% else %}
          {% do cache.update({node_name: node_grains['cache']}) %}
          {% break %}
        {% endif %}
      {% endfor %}
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
    - osd_ips: {{ osd_ips }}
    - mon_ips: {{ mon_ips }}
    - add_osd: {{ add_osd }}
    - mode: 'add_osd'

{%- for node_name, node_grains in salt['mine.get']('ceph*', 'grains.items').iteritems() %}
add new node {{ node_name }}:
  module.run:
    - name: decapod.add_node
    - decapod_ip: {{ pillar['decapod']['decapod_ip'] }}
    - decapod_user: {{ pillar['decapod']['decapod_user'] }}
    - decapod_pass: {{ pillar['decapod']['decapod_pass'] }}
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
    - mode: 'add_osd'
{%- endfor %}