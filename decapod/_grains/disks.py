def decapod_disks():
    import shlex
    from subprocess import check_output

    blockdevs = []
    ssddisks = []
    block_list = check_output(("lsblk", "--exclude", "1,2,7", "-d", "-P", "-o", "NAME,RO,RM,MODEL,ROTA,SIZE", "-x", "SIZE"))
    block_list = block_list.decode("utf-8")
    for blockdev in block_list.splitlines():
        tokens = shlex.split(blockdev)
        current_block = {}
        for token in tokens:
            k, v = token.split("=", 1)
            current_block[k] = v.strip()
        if current_block['ROTA'] == 0:
            ssddisks.append(current_block['NAME'])
        else:
            blockdevs.append(current_block['NAME'])

    return {'ssddisks': ssddisks, 'osddisks': blockdevs}
