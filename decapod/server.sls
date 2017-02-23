# {%- from "decapod/map.jinja" import server with context %}
{%- if server.enabled %}
docker packages:
  pkg.installed:
    - pkgs:
      - docker.io
      - maas-cli

install pip packages:
  pip.installed:
    - names:
      - docker-compose
      - oauth
      - httplib2
      - uuid

login to maas server:
  cmd.run:
    - name: maas login mirantis {{ pillar['decapod']['maas_server'] }} {{ pillar['decapod']['api_key'] }}
    - unless: maas list | grep mirantis > /dev/null

/root/containers/:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

copy containers:
  file.recurse:
    - name: /root/containers
    - source: salt://decapod/files/containers

/root/.env:
  file.managed:
    - source: salt://decapod/files/env
    - template: jinja

load containers:
  cmd.run:
    - name: for i in `ls`; do docker load -i $i; done
    - cwd: /root/containers/
    - unless: for i in migrations cron db-data db frontend controller api; do docker images | grep "decapod/$i"; done

/root/docker-compose.yml:
  file.managed:
    - source: salt://decapod/files/docker-compose.yml
    - template: jinja

/root/containerization/files/devconfigs/:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

/root/ansible_ssh_keyfile.pem:
  file.managed:
    - name: /root/ansible_ssh_keyfile.pem
    - contents: |
        {{ pillar['decapod']['ansible_private_key'] | indent(8) }}
    - mode: '0600'

/root/ansible_ssh_keyfile.pub:
  file.managed:
    - name: /root/ansible_ssh_keyfile.pub
    - contents: |
        {{ pillar['decapod']['ansible_public_key'] }}
    - mode: '0600'

start decapod:
  cmd.run:
    - name: docker-compose up -d
    - cwd: /root/
    - unless: for i in root_frontend_1 root_frontend_1 root_controller_1 root_api_1 root_database_1; do docker inspect -f \{\{\.State.Running\}\} $i; done

/root/migrate.sh:
  file.managed:
    - source: salt://decapod/files/migrate.sh
    - template: jinja
    - mode: '0744'

db migrations:
  cmd.run:
    - name: ./migrate.sh -c root_database_1 apply
    - cwd: /root

deploy nodes:
  module.run:
    - name: decapod.deploy_nodes
    - api_key: {{ pillar['decapod']['api_key'] }}
    - maas_server: {{ pillar['decapod']['maas_server'] }}
    - server_discovery_key: {{ pillar['decapod']['server_discovery_key'] }}
    - decapod_ip: {{ pillar['decapod']['decapod_ip'] }}
    - ansible_public_key: {{ pillar['decapod']['ansible_public_key'] }}

configure cluster:
  module.run:
    - name: decapod.configure_cluster
    - decapod_ip: {{ pillar['decapod']['decapod_ip'] }}
    - decapod_user: {{ pillar['decapod']['decapod_user'] }}
    - decapod_pass: {{ pillar['decapod']['decapod_pass'] }}
    - storage_network: {{ pillar['decapod']['storage_network'] }}
    - frontend_network: {{ pillar['decapod']['frontend_network'] }}
    - management_network: {{ pillar['decapod']['management_network'] }}

{%- endif %}
