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
    {% if pillar['decapod']['http_proxy'] is defined %}
    - proxy: {{ pillar['decapod']['http_proxy'] }}
    {% endif %}


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

start migrations:
  cmd.run:
    - name: docker-compose exec admin decapod-admin migration apply

