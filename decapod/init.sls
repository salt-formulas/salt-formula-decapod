{%- if pillar.decapod is defined %}
include:
{%- if pillar.decapod.server is defined %}
- decapod.server
{%- endif %}
{%- endif %}
