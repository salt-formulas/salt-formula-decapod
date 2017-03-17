{%- if pillar.decapod is defined %}
include:
{%- if pillar.decapod.server is defined %}
- decapod.libs
- decapod.server
{%- endif %}
{%- if pillar.decapod.discover is defined %}
- decapod.discover
{%- endif %}
{%- endif %}
