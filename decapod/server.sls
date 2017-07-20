{%- from "decapod/map.jinja" import server with context %}
{%- if server.enabled %}

{{ server.volume_root }}/db:
  file.directory:
  - makedirs: true

{{ server.volume_root }}/config/config.yaml:
  file.managed:
  - source: salt://decapod/files/decapod.conf
  - template: jinja
  - makedirs: true

{{ server.volume_root }}/key/id_rsa:
  file.managed:
  - mode: 600
  - contents: |
      {{ server.ansible_key|replace('  ', '')|indent(6)}}
  - makedirs: true
{%- endif %}
