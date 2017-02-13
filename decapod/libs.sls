install requirements:
  pkg.installed:
    - names:
      - python-pip
      - libssl-dev

pip fix:
  cmd.run:
    - name: pip install pip==8.1.1 

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
