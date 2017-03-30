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

{{ pillar['decapod']['ansible_public_key'] }}:
  ssh_auth.present:
    - user: ansible
    - enc: ssh-rsa

/usr/share/server_discovery.py:
  file.managed:
    - name: /usr/share/server_discovery.py
    - contents: |
        #-*- coding: utf-8 -*-

        from __future__ import print_function

        import json
        import ssl
        import sys

        try:
            import urllib.request as urllib2
        except ImportError:
            import urllib2

        data = {
            "username": u'ansible',
            "host": sys.argv[1].lower().strip(),
            "id": sys.argv[2].lower().strip()
        }
        data = json.dumps(data).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": '{{ pillar['decapod']['server_discovery_key'] }}',
            "User-Agent": "cloud-init server discovery"
        }

        request = urllib2.Request(u'http://{{ pillar['decapod']['decapod_ip'] }}:9999/v1/server/', data=data, headers=headers)
        request_kwargs = {"timeout": 5}
        if sys.version_info >= (2, 7, 9):
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            request_kwargs["context"] = ctx

        try:
            urllib2.urlopen(request, **request_kwargs).read()
        except Exception as exc:
            sys.exit(str(exc))

        print("Server discovery completed.")
    - mode: '0440'

/usr/share/server_discovery.sh:
  file.managed:
    - name: /usr/share/server_discovery.sh
    - contents: |
        #!/bin/bash
        set -xe -o pipefail

        echo "Date $(date) | $(date -u) | $(date '+%s')"

        main() {
            local ip="$(get_local_ip)"
            local hostid="$(get_local_hostid)"

            python /usr/share/server_discovery.py "$ip" "$hostid"
        }

        get_local_ip() {
            local remote_ipaddr="$(getent ahostsv4 "{{ pillar['decapod']['decapod_ip'] }}" | head -n 1 | cut -f 1 -d ' ')"

            ip route get "$remote_ipaddr" | head -n 1 | rev | cut -d ' ' -f 2 | rev
        }

        get_local_hostid() {
            dmidecode | grep UUID | rev | cut -d ' ' -f 1 | rev
        }

        main
    - mode: '0550'

discover node:
  cmd.run:
    - name: /usr/share/server_discovery.sh


