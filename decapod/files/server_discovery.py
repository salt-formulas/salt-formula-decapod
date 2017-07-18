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
    "username": u'ansible',
    "host": sys.argv[1].lower().strip(),
    "id": sys.argv[2].lower().strip()
}
data = json.dumps(data).encode("utf-8")

headers = {
    "Content-Type": "application/json",
    "Authorization": '""" + server_discovery_key + """',
    "User-Agent": "cloud-init server discovery"
}

request = urllib2.Request(u'http://""" + decapod_ip + """:9999/v1/server/', data=data, headers=headers)
request_kwargs = {"timeout": 5}
if sys.version_info >= (2, 7, 9):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    request_kwargs["context"] = ctx

try:
    urllib2.urlopen(request, **request_kwargs).read()
except Exception as exc:
    sys.exit(str(exc))

print("Server discovery completed.")