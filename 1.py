#! /usr/bin/env python
import sys
import do_scp
import psutil
import time

remote_host = "testcache01.web.sjs.ted"
password = "noSafeNoWork@2014"
remote_path = "/search/odin/daemon/cache/WebCache/data/base"
locale_doc_path = "/search/data1/"
#ret = do_scp.scp_runner(remote_host, password, remote_path + '/*', locale_doc_path, timeout=5)
#print ret
def get_proc_status(pid):
    try:
        p = psutil.Process(pid)
    except:
        return -1
    if (p.status() == "running"):
        return 0
    elif (p.status() == "sleeping"):
        return 1
    return 2
while get_proc_status(3673) is not -1:
    print "e"
    time.sleep(1)
