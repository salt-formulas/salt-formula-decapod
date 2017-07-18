def osds():
    from subprocess import check_output

    output = check_output("df -h | awk '{print $1,$4,$6}' | grep ceph | sed 's#/var/lib/ceph/osd/ceph-##g'", shell=True)
    devices = {}
    for line in output.splitlines():
        device = line.split()
        device[0] = device[0].replace('1','')
        devices[device[0]] = {}
        devices[device[0]]['size'] = device[1]
        devices[device[0]]['nr'] = device[2]

    return { 'osd_devices': devices }