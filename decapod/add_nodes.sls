{% set nodes = salt.saltutil.runner('mine.get',
    tgt='ceph*',
    fun='network.get_hostname',
    tgt_type='glob') -%}

{% set cache = {} %}
{% for node in nodes %}
  {% do cache.update({node: []}) %}
{% endfor %}
{% for node in nodes %}
  {% set osd_grains = salt.saltutil.runner('mine.get',tgt=node,fun='grains.items') %}

  {% if osd_grains[node]['decapod_type'] != 'monitor' %}
    {% for device in pillar['decapod']['cache_devices'] %}
          {% if device in osd_grains[node]['cache'] %}
            {% do cache.update({node: pillar['decapod']['cache_devices']}) %}
          {% endif %}
    {% endfor %}
    {% if cache[node] == [] %}
      {% do  cache.update({node: osd_grains[node]['cache']}) %}
    {% endif %}
  {% endif %}

  add new node {{ node }}:
    module.run:
      - name: decapod.add_node
      - decapod_ip: {{ pillar['decapod']['decapod_ip'] }}
      - decapod_user: {{ pillar['decapod']['decapod_user'] }}
      - decapod_pass: {{ pillar['decapod']['decapod_pass'] }}
      - osd_devices: {{ osd_grains[node]['pools'] | list + pillar['decapod']['ssdpools']| list }}
      - osd_journal_devices: {{ cache[node] | default(osd_grains[node]['cache']) }}
      - ip: {{ osd_grains[node]['fqdn_ip4'] | first }}

{% endfor %}