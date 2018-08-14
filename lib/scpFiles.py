#! /usr/bin/env python
# coding=utf-8

from qwconf import *
from qwqps_runner_new import update_errorlog, get_now_time

import pexpect


def scp_diff_conf(file_path, newconfip, newconfuser, newconfpassw, newconfpath):
    update_errorlog("[%s] try scp rd longdiff_query to test enviroment\n" % get_now_time())
    if os.path.exists(file_path + "/longdiff/longdiff_query"):
        update_errorlog("[%s] %s\n" % (get_now_time(), "long_diffquery  exists, del it"))
        os.popen("rm -rf " + file_path + "/longdiff/longdiff_query")

    passwd_key = '.*assword.*'

    cmdline = 'scp -r %s@%s:%s %s/' % (newconfuser, newconfip, newconfpath, file_path + '/longdiff')
    try:
        child = pexpect.spawn(cmdline)
        expect_result = child.expect([r'assword:', r'yes/no'], timeout=30)
        if expect_result == 0:
            child.sendline(newconfpassw)
        elif expect_result == 1:
            child.sendline('yes')
            child.expect(passwd_key, timeout=30)
            child.sendline(newconfpassw)
        child.expect(pexpect.EOF)
    except Exception as e:
        update_errorlog("[%s] %s, scp rd long_diff failed \n" % (get_now_time(), e))
    update_errorlog("[%s] try scp rd longdiff_query to test enviroment success\n" % get_now_time())
    return 0


if __name__ == '__main__':
    scp_diff_conf("/search/odin/daemon", "webqw01.web.djt.ted", "guest", "Sogou@)!$", "/opt/guest/longdiff_query")

