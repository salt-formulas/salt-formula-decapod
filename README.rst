
===============
Decapod formula
===============

Decapod is intendend to simplify deployment and lifecycle management of Ceph.


Sample pillars
==============

Decapod Server

.. code-block:: yaml

   decapod:
    server_discovery_key: https://github.com/Mirantis/ceph-lcm/blob/master/containerization/files/devconfigs/config.yaml api['server_discovery_token']
    decapod_ip: 127.0.0.1

    # as default, all ssd disks will be configured as journal devices,
    # if you want to use them as osd you need to define ssdpools and ssd_size
    ssdpools:
      - /dev/sdb
      - /dev/sdc
      - /dev/sdd
      - /dev/sde
    ssd_size: 1.1T
    # If you are using ssdpools variable you also need to specify journal devices
    cache_devices:
      - /dev/xvde1
      - /dev/xvde2

    # decapod needs ansible user to work
    ansible_private_key:
    ansible_public_key:

    decapod_user: "root"
    decapod_pass: "root"

    # ceph internal network
    storage_network: "192.168.0.0/24"
    # ceph frontend network
    frontend_network: "192.168.1.0/24"

    # internal network interface on physical and virtual nodes
    phys_mon_interface: "eth0.1"
    vm_mon_interface: "ens2"

    journal_size: 512
    max_open_files: 131072


Decapod Client

.. code-block:: yaml

    decapod:
      client:
        admin_key: AQCvCbtToC6MDhAATtuT70Sl+DymPCfDSsyV4w==
        users:
        - nova:
            key: AQCvCbtToC6MDhAATtuT70Sl+DymPCfDSsyV4w==
            caps:
              osd: 'allow r'
              mon: 'allow class-read object_prefix rbd_children, allow rwx pool=nova'
        - cinder:
                key: AQCvCbtToC6MDhAATtuT70Sl+DymPCfDSsyV4w==
                caps:
                  osd: 'allow r'
                  mon: 'allow class-read object_prefix rbd_children, allow rwx pool=cinder'
          pools:
            - nova:
                rule: 0
                pg: 100
            - cinder:
                rule: 0
                pg: 100


Decapod Discover

.. code-block:: yaml

    decapod:
        server_discovery_key: https://github.com/Mirantis/ceph-lcm/blob/master/containerization/files/devconfigs/config.yaml api['server_discovery_token']
        decapod_ip: 127.0.0.1
        ansible_public_key:



Read more
=========

* http://decapod.readthedocs.io/en/latest/

Documentation and Bugs
======================

To learn how to install and update salt-formulas, consult the documentation
available online at:

    http://salt-formulas.readthedocs.io/

In the unfortunate event that bugs are discovered, they should be reported to
the appropriate issue tracker. Use Github issue tracker for specific salt
formula:

    https://github.com/salt-formulas/salt-formula-letsencrypt/issues

For feature requests, bug reports or blueprints affecting entire ecosystem,
use Launchpad salt-formulas project:

    https://launchpad.net/salt-formulas

You can also join salt-formulas-users team and subscribe to mailing list:

    https://launchpad.net/~salt-formulas-users

Developers wishing to work on the salt-formulas projects should always base
their work on master branch and submit pull request against specific formula.

    https://github.com/salt-formulas/salt-formula-letsencrypt

Any questions or feedback is always welcome so feel free to join our IRC
channel:

    #salt-formulas @ irc.freenode.net
