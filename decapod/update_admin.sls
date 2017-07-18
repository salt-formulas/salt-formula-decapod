update admin keyring:
  file.managed:
    - name: /etc/ceph/ceph.client.admin.keyring
    - contents: |
        [client.admin]
          key = {{ pillar['decapod']['client']['admin_key'] }}
    - mode: '0600'