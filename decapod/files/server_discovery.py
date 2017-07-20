#-*- coding: utf-8 -*-

from __future__ import print_function

import json
import ssl
import sys

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

data = {
    "username": 'ansible',
    "host": sys.argv[1].lower().strip(),
    "id": sys.argv[2].lower().strip()
}
headers = {
    "Content-Type": "application/json",
    "Authorization": '67cf31d8-aca4-471f-891f-8327c4ad9abd',
    "User-Agent": "cloud-init server discovery"
}

def get_response(url, data=None):
    if data is not None:
        data = json.dumps(data).encode("utf-8")
    request = urllib2.Request(url, data=data, headers=headers)
    request_kwargs = {"timeout": 20}
    if sys.version_info >= (2, 7, 9):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        request_kwargs["context"] = ctx
    try:
        return urllib2.urlopen(request, **request_kwargs).read()
    except Exception as exc:
        print("Cannot request {0}: {1}".format(url, exc))


response = get_response('http://{{ pillar.decapod.discover.decapod_address }}:9999/v1/server/', data)
if response is None:
    sys.exit("Server discovery failed.")
print("Server discovery completed.")
