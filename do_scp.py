#! /usr/bin/env python
#coding=utf-8

import pexpect
import sys

def scp_runner(remotehost, passwd, src_path, dst_path, timeout = 5*60):
    keys = [ 'authenticity', '[Pp]assword:', pexpect.EOF, pexpect.TIMEOUT ]
    command = 'scp -r %s:%s %s/' % (remotehost, src_path, dst_path)
    print command
    try:
        child = pexpect.spawn(command, timeout = timeout)
        child.logfile = sys.stdout
    except Exception, e:
        print e
        return 1
    index = child.expect(keys)
    if index == 0:
        child.sendline('yes')
        index = child.expect(keys)
        print 0
    elif index == 2:
        child.sendline(passwd)
        index = child.expect(keys)
        print 2
    elif index == 2 or index == 3:  
        return 2

    if index == 1:
        child.sendline(passwd)
        index = child.expect(keys)
        print 11
    if index == 2:
        #success
        return 0
    elif index == 3:
        #timeout
        return 3
    elif index == 1:
        #password error
        return 4

    if index == 2:
        return 0
