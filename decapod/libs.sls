install requirements:
  pkg.installed:
    - names:
      - libssl-dev

/root/get-pip.py:
  file.managed:
    - source: salt://decapod/files/get-pip.py
    - name: /root/get-pip.py

install pip:
  cmd.run:
    - name: python get-pip.py

/root/decapodlib:
  file.directory:
    - user: root
    - group: root
    - mode: 755
    - makedirs: True

copy lib files:
  file.recurse:
    - name: /root/decapodlib
    - source: salt://decapod/files/lib

install lib:
  cmd.run:
    - name: pip install decapodlib/decapodlib*.whl decapodlib/decapod_cli*.whl
    - cwd: /root/
    - unless: type decapod >/dev/null 2>&1
