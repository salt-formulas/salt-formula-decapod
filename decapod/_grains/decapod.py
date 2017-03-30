def decapod():
    import shlex
    from subprocess import check_output
    import os
    import lsb_release
    import re

    pools = []
    cache = []

    if lsb_release.get_lsb_information()['RELEASE'] == '16.04':
        block_list = check_output(("lsblk", "--exclude", "1,2,7", "-d", "-P", "-o", "NAME,RO,RM,MODEL,ROTA,SIZE,MIN-IO", "-x", "SIZE"))
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

        hostname = os.uname()[1]
        match = re.search("ceph-mon", hostname)
        if match:
            decapod_type = 'monitor'
            return {'pools': pools, 'cache': cache, 'decapod_type': decapod_type}
        match = re.search('ceph[0-9]*', hostname)
        if match:
            decapod_type = 'osd'
            return {'pools': pools, 'cache': cache, 'decapod_type': decapod_type}
        else:
            decapod_type = 'other'
            return {'pools': pools, 'cache': cache, 'decapod_type': decapod_type}
