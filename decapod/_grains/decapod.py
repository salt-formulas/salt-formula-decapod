def decapod():
    import shlex
    import subprocess
    import os
    import lsb_release
    import re

    pools = []
    cache = []

    if lsb_release.get_lsb_information()['RELEASE'] == '16.04':
        block_list = subprocess.check_output(("lsblk", "--exclude", "1,2,7", "-d", "-P", "-o", "NAME,RO,RM,MODEL,ROTA,SIZE,MIN-IO", "-x", "SIZE"))
        block_list = block_list.decode("utf-8")
        for blockdev in block_list.splitlines():
            tokens = shlex.split(blockdev)
            current_block = {}
            for token in tokens:
                k, v = token.split("=", 1)
                current_block[k] = v.strip()
            if current_block['NAME'] == 'sda' or current_block['NAME'] == 'vda':
                continue
            if current_block['ROTA'] == '0':
                cache.append('/dev/' + current_block['NAME'])
                continue
            if current_block['MIN-IO'] == '4096':
                cache.append('/dev/' + current_block['NAME'])
                continue
            else:
                pools.append('/dev/' + current_block['NAME'])

        cmd = "route | grep default   | awk '{print $8}'"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        local_int = ps.communicate()[0].rstrip("\n")
        cmd = "ifconfig " + local_int + "| grep -v inet6 | grep inet | tr ':' ' ' | awk '{print $3}'"
        ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        local_ip = ps.communicate()[0].rstrip("\n")

        hostname = os.uname()[1]
        match = re.search("ceph-mon", hostname)
        if match:
            decapod_type = 'monitor'
            return {'pools': pools, 'cache': cache, 'decapod_type': decapod_type, 'decapod_mgmt_ip': local_ip}
        match = re.search('ceph[0-9]*', hostname)
        if match:
            decapod_type = 'osd'
            return {'pools': pools, 'cache': cache, 'decapod_type': decapod_type, 'decapod_mgmt_ip': local_ip}
        else:
            decapod_type = 'other'
            return {'pools': pools, 'cache': cache, 'decapod_type': decapod_type}
