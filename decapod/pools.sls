{% for pool in pillar['decapod']['client']['pools'] %}
create pool {{ pool }}:
  cmd.run:
    - name: ceph osd pool create {{ pool }} {{ pillar['decapod']['client']['pools'][pool]['pg'] }}

set crush ruleset {{ pool }}:
  cmd.run:
    - name: ceph osd pool set {{ pool }} crush_ruleset {{ pillar['decapod']['client']['pools'][pool]['rule'] }}
{% endfor %}


{% for user in pillar['decapod']['client']['users'] %}
create keyring {{ user }}:
  cmd.run:
    - name: ceph-authtool -C {{ user }}.keyring
    - cwd: /root

add key and caps {{ user }}:
  cmd.run:
    - name: ceph-authtool -a {{ pillar['decapod']['client']['users'][user]['key'] }} -n client.{{ user }}
            --cap mon '{{ pillar['decapod']['client']['users'][user]['caps']['mon'] }}'
            --cap osd '{{ pillar['decapod']['client']['users'][user]['caps']['osd'] }}' {{ user }}.keyring
    - cwd: /root

import keyring {{ user }}:
  cmd.run:
    - name: ceph auth import -i {{ user }}.keyring
    - cwd: /root
{% endfor %}

change temp admin key:
  cmd.run:
    - name: ceph-authtool -C admin.keyring
    - cwd: /root

change admin key:
  cmd.run:
    - name: ceph-authtool -a {{ pillar['decapod']['client']['admin_key'] }} -n client.admin
            --cap mon 'allow *'
            --cap mds 'allow *'
            --cap osd 'allow *' admin.keyring
    - cwd: /root

import admin keyring:
  cmd.run:
    - name: ceph auth import -i admin.keyring
    - cwd: /root


