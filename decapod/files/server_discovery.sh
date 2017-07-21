#!/bin/bash
set -xe -o pipefail

echo "Date $(date) | $(date -u) | $(date '+%s')"

main() {
    local ip="$(get_local_ip)"
    local hostid="$(get_local_hostid)"

    python /usr/share/server_discovery.py "$ip" "$hostid"
}

get_local_ip() {
    local remote_ipaddr="$(getent ahostsv4 "{{ pillar.decapod.discover.decapod_address }}" | head -n 1 | cut -f 1 -d ' ')"

    ip route get "$remote_ipaddr" | head -n 1 | rev | cut -d ' ' -f 2 | rev
}

get_local_hostid() {
    dmidecode | grep UUID | rev | cut -d ' ' -f 1 | rev
}

main
