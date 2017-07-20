ansible user:
  user.present:
    - name: ansible
    - fullname: ansible
    - shell: /bin/bash
    - home: /home/ansible
    - groups:
      - sudo

/etc/sudoers.d/99-ansible-user:
  file.managed:
    - name: /etc/sudoers.d/99-ansible-user
    - contents: |
        ansible ALL=(ALL) NOPASSWD:ALL
    - mode: '0600'

{{ pillar.decapod.discover.ansible_public_key }}:
  ssh_auth.present:
    - user: ansible
    - enc: ssh-rsa

/etc/rc.local:
  file.managed:
    - mode: 755
    - source: salt://redep/files/rc.local
    - template: jinja

/usr/share/server_discovery.sh:
  file.managed:
    - mode: 755
    - source: salt://redep/files/server_discovery.sh
    - template: jinja

/usr/share/server_discovery.py:
  file.managed:
    - source: salt://redep/files/server_discovery.py
    - template: jinja

run_discover:
  cmd.run:
    - name: /usr/share/server_discovery.sh
