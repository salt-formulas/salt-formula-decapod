{%- if pillar.decapod is defined %}
include:
{%- if pillar.decapod.server is defined %}
- decapod.libs
- decapod.server
# - decapod.cleanup
{%- endif %}
{%- endif %}
