#! /usr/bin/env python
#coding=utf-8

import os
import sys
import MySQLdb
import time
import subprocess
from conf import *

import asycommands
import svnpkg


import psutil
import hashlib
import signal

import pexpect

db = MySQLdb.connect(database_host,database_user,database_pass,database_data)
cursor = db.cursor()

mission_id = int(sys.argv[1])

def get_now_time():
    timeArray = time.localtime()
    return  time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

def get_material():

#newconfpath | newconfip | newconfpassw | newconfuser | newdataip | newdatapassw | newdatauser | newdatapath

    sql = "SELECT testsvn, basesvn, testitem, newconfip, newconfuser, newconfpassw, newconfpath, newdataip, newdatauser, newdatapassw, newdatapath, force_update_test_svn, force_update_base_svn, just_run_test, just_run_base, press_qps, press_time FROM %s where id='%d'" % (database_table,mission_id)
    cursor.execute(sql)
    data = cursor.fetchone()
    sql = "UPDATE %s set start_time='%s', status = 2 where id=%d" % (database_table, get_now_time() ,mission_id)
    try:
        cursor.execute(sql)
        db.commit()
    except:
        pass
    print "data", data
    return data

def update_errorlog(log):
    print log.replace('\n', '')
    log = log.replace("'", "\\'")
    sql = "UPDATE %s set errorlog=CONCAT(errorlog, '%s') where id=%d;" % (database_table, log, mission_id)
    cursor.execute(sql)
    data = cursor.fetchone()
    try:
        db.commit()
    except:
        print "error"
    return data


def set_status(stat):
    sql = "UPDATE %s set status=%d, end_time='%s' where id=%d" % (database_table, stat, get_now_time(), mission_id)
    cursor.execute(sql)
    db.commit()
    if (stat != 1):
        clean_proc()


def unlock_freez():
    ### need unlock here 

    asycmd = asycommands.TrAsyCommands(timeout=300)
    unfreez_log = ""
    for iotype, line in asycmd.execute_with_data(['sh', 'freeze_fx.sh', 'unlock'], shell=False, cwd = root_path):
        if iotype is 2:
            unfreez_log += line + "\n"
    if (asycmd.return_code() == 2):
        update_errorlog(unfreez_log)
        return 2
    update_errorlog("[%s] unfreez successaa\n" % get_now_time())


def clean_proc():
    os.popen('killall -9 memcached lt-memdb_daemon sggp lt-webcached')
    time.sleep(3)

    return


def sync_ol_data_to_local(data_path):
    if os.path.exists(data_path) == False:
        print "tmp_ol_data path not exists, mkdir -p"
        update_errorlog("[%s] %s\n" % (get_now_time(), "tmp_ol_data path not exists, mkdir -p")) 
        os.popen("mkdir -p " + data_path)

    update_errorlog("[%s] start rsync ol_data to local\n" % get_now_time())

    rsync_path = online_path
    if (rsync_path[0:1] == "/"):
        rsync_path = rsync_path[1:]
    if (rsync_path[len(rsync_path)-1:] != "/"):
        rsync_path = rsync_path + "/"
    rsync_path = rsync_path + "data/"
    arg2 = data_path
    if (data_path[len(data_path)-1:] != "/"):
        arg2 = data_path + "/"

    arg = "%s::%s" % (online_host, rsync_path)
    stdlog = ""
    errlog = ""
    asycmd = asycommands.TrAsyCommands(timeout=30*60)
#    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', arg, arg2], shell=False):
        if (iotype is 1):
            stdlog += line + '\n'
            print line
        elif (iotype is 2):
            errlog += line + '\n'
    if (asycmd.return_code() != 0):
        update_errorlog("[%s] rsync ol_data to local Error\n" % get_now_time())
        update_errorlog(errlog)
        return 1
    update_errorlog("[%s] rsync ol_data to local success\n" % get_now_time())
    return 0
 
    
def sync_ol_conf_to_local(conf_path):
    if os.path.exists(conf_path) == False:
#        print "tmp_ol_conf path not exists, mkdir -p"
        update_errorlog("[%s] %s\n" % (get_now_time(), "tmp_ol_conf path not exists, mkdir -p")) 
        os.popen("mkdir -p " + conf_path)

    update_errorlog("[%s] start rsync ol_conf to local\n" % get_now_time())

    rsync_path = online_path
    if (rsync_path[0:1] == "/"):
        rsync_path = rsync_path[1:]
    if (rsync_path[len(rsync_path)-1:] != "/"):
        rsync_path = rsync_path + "/"
    rsync_path = rsync_path + "conf/"
    arg2 = conf_path
    if (conf_path[len(conf_path)-1:] != "/"):
        arg2 = conf_path + "/"

    arg = "%s::%s" % (online_host, rsync_path)
    stdlog = ""
    errlog = ""
    asycmd = asycommands.TrAsyCommands(timeout=30*60)
#    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', arg, arg2], shell=False):
        if (iotype is 1):
            stdlog += line + '\n'
            print line
        elif (iotype is 2):
            errlog += line + '\n'
    if (asycmd.return_code() != 0):
        update_errorlog("[%s] rsync ol_conf to local Error\n" % get_now_time())
        update_errorlog(errlog)
        return 1
    update_errorlog("[%s] rsync ol_conf to local success\n" % get_now_time())
    return 0




def checkcode_env(path, svn):
    print "path 1111", path
    if os.path.exists(path) == False:
#        print "tmp_ol_conf path not exists, mkdir -p"
        update_errorlog("[%s] %s%s\n" % (get_now_time(), path, " not exists, mkdir -p"))
        os.popen("mkdir -p " + path)

    update_errorlog("[%s] start check code [%s]\n" %(get_now_time(), path))
    
    mysvn = svnpkg.SvnPackage("qa_svnreader", "New$oGou4U!")

    for line in svn.split("\n"):
#        print line

#        if line == "":
#            continue
#        if (line.find(';') == 0):
#            continue
        pos = line.find('=')
#        if (pos == -1 and line.find('http://') == 0):
#            line = ".=" +line
#            pos = 1
        key = line[0:pos]
        value = line[pos+1:]
        if (value.find('http://') != 0):
            update_errorlog("[%s] url format error: %s\n" % (get_now_time(), line))
            return -1
        key_path = os.path.join(path, key)

        url = ""
        if (mysvn.svn_info(key_path) != 0):
        #no path, then checkout
            ret = mysvn.svn_co(value, key_path)
            if (ret != 0):
                update_errorlog("[" + get_now_time() + "] check " + key + " error\n" + mysvn.get_errlog())
                return 1
            else:
                mysvn.svn_info(key_path)
                for log_line in mysvn.get_stdlog().split('\n'):
                    if (log_line.find("URL:") == 0):
                        url = log_line.split(' ')[1]
                        break
                update_errorlog("[" + get_now_time() + "] check ok " + key + "->" + url + "\n")
        else:
        #path exists, then switch
            ret = mysvn.svn_sw(value, key_path)
            if (ret != 0):
                update_errorlog("[" + get_now_time() + "] check " + key + " error\n" + mysvn.get_errlog())
                return 1
            else:
                mysvn.svn_info(key_path)
                for log_line in mysvn.get_stdlog().split('\n'):
                    if (log_line.find("URL:") == 0):
                        url = log_line.split(' ')[1]
                        break
                update_errorlog("[" + get_now_time() + "] check ok " + key + "->" + url + "\n")
    update_errorlog("[%s] checkout success\n" % get_now_time())
    return 0
    # all code checkout ok, compile


def make_env(path):
    asycmd = asycommands.TrAsyCommands(timeout=300)
#    asycmd_list.append(asycmd)
    make_log = ""
    for iotype, line in asycmd.execute_with_data(['make', '-j8'], shell=False, cwd = path):
        if iotype is 2:
            make_log += line + "\n"
    if (asycmd.return_code() != 0):#timeout or error, then try again
        make_log = ""
        for iotype, line in asycmd.execute_with_data(['make' '-j8'], shell=False, cwd = path):
            if iotype is 2:
                make_log += line
    if (asycmd.return_code() != 0):
        update_errorlog(make_log)
        return 2
    update_errorlog("[%s] make success\n" % get_now_time())
    return 0


def cp_ol_env(data_path, env_path, conf_path):
# = cp_ol_env(ol_data_path, test_path)
#             /search/odin/daemon/autoCacheQPS/tmp_data
#             /search/odin/daemon/autoCacheQPS/cache_test
    asycmd = asycommands.TrAsyCommands(timeout=30*60)
#    asycmd_list.append(asycmd)
    os.popen("rm -rf " + env_path + "WebCache/data")
    ### rsync ol_data to local
    errlog = ""
    for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', data_path + "/", env_path + "/WebCache/data/"], shell=False):
        if iotype is 2:
            errlog += line + '\n'
#            print "line: ", line

    if (asycmd.return_code() != 0):
        return 1
    update_errorlog("[%s] sync ol_data to local success\n" % get_now_time())

    ### cp ol_dev_conf to local
    if os.path.exists(env_path + "/WebCache/conf/") == False:
        print "local conf path not exists, mkdir -p"
        update_errorlog("[%s] %s\n" % (get_now_time(), "local conf path not exists, mkdir -p")) 
        os.popen("mkdir -p " + env_path + "/WebCache/conf")

    if os.path.exists(env_path + "/WebCache/log/data/") == False:
        print "local log path not exists, mkdir -p"
        update_errorlog("[%s] %s\n" % (get_now_time(), "local log path not exists, mkdir -p")) 
        os.popen("mkdir -p " + env_path + "/WebCache/log/data")

    os.popen("cp %s/cache_dev.cfg %s/WebCache/conf/" % (conf_path, env_path))
    os.popen("cp %s/start.sh %s/WebCache/" % (root_path, env_path))
    update_errorlog("[%s] sync ol_dev_conf to local success\n" % get_now_time())

    return 0

def cp_press_conf_env(env_path):
    ### cp press_conf to local
    os.popen("cp %s %s/WebCache/conf/" % (press_conf, env_path))
    update_errorlog("[%s] sync press_conf to local success\n" % get_now_time())

    return 0


def cp_own_env(des_path, ip, user, passw, old_path, type_):
#                   /search/odin/daemon/autoCacheQPS/cache_test
    update_errorlog("[%s] try scp new_data to enviroment\n" % get_now_time())

    passwd_key = '.*assword.*'
# scp -r root@10.134.99.71:/search/odin/dddd /search/daemon/cache_test/WebCache/data/

    if type_ == "data":
    
        cmdline = 'scp -r %s@%s:%s/* %s/WebCache/data/' %(user, ip, old_path, des_path)
        print 'cmdline: ', cmdline

    else:
        cmdline = 'scp -r %s@%s:%s/* %s/WebCache/conf/' %(user, ip, old_path, des_path)
        print 'cmdline: ', cmdline

    try:
        child=pexpect.spawn(cmdline)
        expect_result = child.expect([r'assword:',r'yes/no'],timeout=30)
        if expect_result == 0:
#    print 111
            child.sendline(passw)

        elif expect_result ==1:
#    print 2222
            child.sendline('yes')
            child.expect(passwd_key,timeout=30)
            child.sendline(passw)
        child.expect(pexpect.EOF)    

    except Exception, e:
        update_errorlog("[%s] %s, scp something\n" % (get_now_time(), e))

    return 0

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



def wait_to_die(pid, interval):
    while get_proc_status(pid) is not -1:
        print "[%s] proc_status: %s" %(get_now_time(), get_proc_status(pid))
        time.sleep(interval)
        print "abcd"
        print "[%s] sleep_interval: %s" %(get_now_time(), interval)
        if (interval > 10):
            interval = interval/2


def stop_proc(pid):
    os.popen("/bin/kill -9 %d" % pid)
    wait_to_die(pid, 2)
    return 0


def lanch(path, start_script, port, log):
#   lanch(mem_path, 'restart_memdb.sh', -1, tmp)
# rules: start_script must put pid in `PID` file: echo $! > PID
# return a tuple(retcode, pid)

    pid = -1
    asycmd = asycommands.TrAsyCommands(timeout=30)
#    asycmd_list.append(asycmd)
    child = subprocess.Popen(['/bin/sh', start_script], shell=False, cwd = path, stderr = subprocess.PIPE)
    child.wait()

    time.sleep(60)

    if (child.returncode != 0):
        log.append(child.stderr.read())
        return (-1, pid)
    for iotype, line in asycmd.execute_with_data(['/bin/cat', path + "/PID"], shell=False):
        if (iotype == 1 and line != ""):
            try:
                if (pid == -1):
                    pid = int(line)
                else:
                    tmp = int(line)
                    pid = max(pid, tmp)
            except:
                continue
    if (pid == -1):
        return (-2, pid)
    proc = None
    try:
        proc = psutil.Process(pid)
    except:
        log.append("process %d is not alive" % pid)
        return (-3, pid)
    if (port is -1):
        return (0, pid)
    is_alive = True
    start_time = 0
#    proc_list.append(pid)
    while is_alive:
        try:
            conn_list = proc.connections()
        except:
            is_alive = False
            break
        listened = False
        for conn in conn_list:
            if (conn.status == "LISTEN" or conn.status == "NONE") and conn.laddr[1] == port:
                listened = True
                break
        if listened:
            break
        time.sleep(1)
        start_time += 1
    if not is_alive:
        log.append("process start failed")
#        proc_list.remove(pid)
        return (-3, pid)
    return (start_time, pid)


#test_path /search/odin/daemon/autoCacheQPS/cache_test

def run_performace(path, x):
    cost = []


    ### need sh freez.sh lock

    asycmd = asycommands.TrAsyCommands(timeout=120)
    freez_log = ""
    for iotype, line in asycmd.execute_with_data(['sh', 'freeze_fx.sh', 'lock'], shell=False, cwd = root_path):
        if iotype is 2:
            freez_log += line + "\n"
    if (asycmd.return_code() == 1):
        update_errorlog(freez_log)
        update_errorlog("[%s] freez error in using\n" % get_now_time())


        sql = "UPDATE %s set status=3, end_time='%s' where id=%d" % (database_table, get_now_time(), mission_id)
        cursor.execute(sql)
        db.commit()

        sys.exit()
#        return 2
    update_errorlog("[%s] freez success\n" % get_now_time())

    ###


    ret = performance_once(path, cost)
    if (ret !=0):
        return ret
    set_content_to_x(cost, x)

    ### need unlock here 

    unlock_freez() 

    """
    asycmd = asycommands.TrAsyCommands(timeout=300)
    unfreez_log = ""
    for iotype, line in asycmd.execute_with_data(['sh', 'freeze_fx.sh', 'unlock'], shell=False, cwd = root_path):
        if iotype is 2:
            unfreez_log += line + "\n"
    if (asycmd.return_code() == 2):
        update_errorlog(unfreez_log)
        return 2
    update_errorlog("[%s] unfreezzzz success\n" % get_now_time())
    """
    ###

    return 0


def set_content_to_x(content, x):
    tmp = []
    total_content = ""
    if (type(content) == type(tmp)):
        for line in content:
            total_content += line + '\n'
    elif (type(content) == type(total_content)):
        total_content = content
    sql = "UPDATE %s set %s='%s' where id=%d" % (database_table, x, total_content.decode('gbk').encode('utf8'), mission_id)
    print sql
    cursor.execute(sql)
    db.commit()


def performance_once(path, performance_result):
    asycmd = asycommands.TrAsyCommands(timeout=120)
#    asycmd_list.append(asycmd)

    # kill cache
    for iotype, line in asycmd.execute_with_data(['ps', '-ef|', 'grep', 'lt-webcached|', 'grep', '-v', 'color'], shell=False):
        if (line.find('lt-webcached') != -1):
            pid = int(line.split('     ')[1])
            stop_proc(pid)
    # kill all mem
    os.popen('killall -9 memcached lt-memdb_daemon sggp lt-webcached')
    # start mem
    tmp = []
    try:
        lanch(mem_path, 'restart_memdb.sh', -1, tmp)
    except:
        return -2
#    tools_path = os.path.join(root_path, "package/sggp")
    log = []
    # start cache
    print "start cache"
    (ret, cache_pid) = lanch(path + "/WebCache", "start.sh", 28001, log)
    if (ret < 0):
        time.sleep(0.5)
        up_log = ""
        for line in log:
            up_log += "[%s] %s" % (get_now_time(), line + '\n')
        update_errorlog("%s\n" % (up_log))
        for iotype, line in asycmd.execute_with_data(['/bin/tail', '-50', path + "/WebCache/err"], shell=False):
            up_log += line +'\n'
        update_errorlog(up_log.decode('gbk').encode('utf-8').replace("'", "\\'"))
        print path + "/WebCache/err"
        return -1
    update_errorlog("[%s] cache Start OK, cost %d s\n" % (get_now_time(), ret))
#    proc_list.append(sh_pid)

    # Start PressTool
    log = []
    (ret, tools_pid) = lanch(sggp_path, "start_cache.sh", -1, log)
    print "1_tools_pid: ", tools_pid
    if (ret < 0):
        time.sleep(0.5)
        up_log = ""
        for line in log:
            up_log += "[%s] %s" % (get_now_time(), line + '\n')
        update_errorlog("%s\n" % (up_log))
        up_log = ""
        for iotype, line in asycmd.execute_with_data(['/bin/tail', '-50', sggp_path + "/err.cache"], shell=False):
            up_log += line + '\n'
        update_errorlog(up_log.decode('gbk').encode('utf-8').replace("'", "\\'"))
        return -1
    update_errorlog("[%s] PressTool Start OK\n" % get_now_time())
#    proc_list.append(tools_pid)
    update_errorlog("[%s] Wait PressTool...\n" % get_now_time())

    # Wait PressTool Stop
    wait_to_die(tools_pid, 5*60)
    print "[%s] 2_tools_pid: %s" %(get_now_time(), tools_pid)
    update_errorlog("[%s] PressTool stoped\n" % get_now_time())
    # Stop cache
    stop_proc(cache_pid)
    update_errorlog("[%s] Cache stoped\n" % get_now_time())
    # Stop mem
    os.popen('killall -9 memcached lt-memdb_daemon sggp lt-webcached')

    return get_performance(path + '/WebCache/err', performance_result)

def get_performance(log_file, performance):
    if (os.path.exists(log_file) is False):
        performance.append(log_file + " is not exists")
        return -1

    asycmd = asycommands.TrAsyCommands(timeout=180)
#    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['python', cost_tool, log_file], shell=False):
        performance.append(line)
    if (asycmd.return_code() != 0):
        return asycmd.return_code()
    return 0



def test():
    test_path = root_path + test_path_1

    (testsvn, basesvn, testitem, newconfip, newconfuser, newconfpassw,newconfpath, newdataip, newdatauser, newdatapassw, newdatapath, force_update_test_svn, force_update_base_svn, just_run_test, just_run_base) = get_material()

    ret = checkcode_env(test_path, testsvn)

    print ret


def configure_sggp(sggp_conf_file,qps,time):
    if qps == '' or qps > 100:
        qps = 100
    if time == '' or time > 30:
        time = 15

    os.popen("sed -i 's/press_time=.*/press_time=%s/g' %s" %(time, sggp_conf_file))
    os.popen("sed -i 's/press_qps=.*/press_qps=%s/g' %s" %(qps, sggp_conf_file))
    update_errorlog("[%s] configure sggp_conf success\n" % get_now_time())
    
    return 0





def main():
    type_1 = "data"
    type_2 = "conf"
 
    test_path = root_path + test_path_1
    base_path = root_path + base_path_1

    ol_data_path = root_path + ol_data_path_1
    ol_conf_path = root_path + ol_conf_path_1

    print "test_path", test_path
    print "base_path", base_path

    print "ol_data_path", ol_data_path
    print "ol_conf_path", ol_conf_path

    print "mission_id", mission_id

    (testsvn, basesvn, testitem, newconfip, newconfuser, newconfpassw,newconfpath, newdataip, newdatauser, newdatapassw, newdatapath, force_update_test_svn, force_update_base_svn, just_run_test, just_run_base, press_qps, press_time) = get_material()
    
    print "testsvn", testsvn
    print "basesvn", basesvn
    print "testitem", testitem
    print "newconfip", newconfip
    print "newconfuser", newconfuser
    print "newconfpassw", newconfpassw
    print "newconfpath", newconfpath
    print "newdataip", newdataip
    print "newdatauser", newdatauser
    print "newdatapassw", newdatapassw
    print "newdatapath", newdatapath
    print "force_update_test_svn", force_update_test_svn
    print "force_update_base_svn", force_update_base_svn
    print "just_run_test", just_run_test
    print "just_run_base", just_run_base

    print "press_qps", press_qps
    print "press_time", press_qps

    ####configure sggp/ACE_Pressure_CACHE.ini

    ret_configure_sggp = configure_sggp(sggp_conf,press_qps,press_time)
    if ret_configure_sggp != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "configure sggp_conf has some error, pls check"))
        set_status(3)
        return -1
   


    if just_run_test == 1 and just_run_base == 1:
        update_errorlog("[%s] %s\n" % (get_now_time(), "You choise just test and just base at the same time. which one do you want, test or base?"))
        set_status(3)
        return -1
    
    ret_sync_ol_data = sync_ol_data_to_local(ol_data_path)
    if ret_sync_ol_data != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_ol_data_to_local has some error, pls check"))
        set_status(3)
        return -1

    ret_sync_ol_conf = sync_ol_conf_to_local(ol_conf_path)
    if ret_sync_ol_conf != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_ol_conf_to_local has some error, pls check"))
        set_status(3)
        return -1


#### just run test
    if just_run_test == 1 and just_run_base == 0:

        update_errorlog("[%s] %s\n" % (get_now_time(), "try start test only"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build test enviroment"))
        ### check code
        try:
            print "testsvn", testsvn
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try check code"))
            ret = checkcode_env(test_path, testsvn)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test check code ok"))
        
        ### make
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try make"))
            ret = make_env(test_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test make ok"))
        
        ### rsync ol_data && ol_dev_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp ol_data and ol_dev_conf"))
            ret = cp_ol_env(ol_data_path, test_path, ol_conf_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp ol_data and ol_dev_conf ok"))

        ### rsync press_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp press_conf"))
            ret = cp_press_conf_env(test_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp press_conf ok"))

        ### rsync own_data
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp own_data"))
            if (newdataip != "" and newdatauser != "" and newdatapassw != "" and newdatapath != ""):
                ret = cp_own_env(test_path, newdataip, newdatauser, newdatapassw, newdatapath, type_1)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_data error"))
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_data ok"))

        ### rsync own_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp own_conf"))
            if (newconfip != "" and newconfuser != "" and newconfpassw != "" and newconfpath != ""):
                ret = cp_own_env(test_path, newconfip, newconfuser, newconfpassw, newconfpath, type_2)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_conf error"))
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_conf ok"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "test env build ok"))
        
        ### start perform
        if (testitem == 1):#need to run performance
            try:
                ret = run_performace(test_path, "cost_test")
                if (ret != 0):
                    set_status(3)
                    return -1
            except Exception, e:
                update_errorlog("[%s] %s\n" % (get_now_time(), e))
                set_status(3)
                return -1
            if (ret != 0):
                set_status(3)
                return 5
        set_status(4)
        return 0



###### just run base

    if just_run_test == 0 and just_run_base == 1:


        update_errorlog("[%s] %s\n" % (get_now_time(), "try start base only"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build base enviroment"))
        ### check code
        try:
            print "basesvn", basesvn
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try check code"))
            ret = checkcode_env(base_path, basesvn)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base check code ok"))
        
        ### make
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try make"))
            ret = make_env(base_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base make ok"))
        
        ### rsync ol_data && ol_dev_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try cp ol_data and ol_dev_conf"))
            ret = cp_ol_env(ol_data_path, base_path, ol_conf_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base cp ol_data and ol_dev_conf ok"))

        ### rsync press_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try cp press_conf"))
            ret = cp_press_conf_env(base_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base cp press_conf ok"))

        ### rsync own_data
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try cp own_data"))
            if (newdataip != "" and newdatauser != "" and newdatapassw != "" and newdatapath != ""):
                ret = cp_own_env(base_path, newdataip, newdatauser, newdatapassw, newdatapath, type_1)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            update_errorlog("[%s] %s\n" % (get_now_time(), "base cp own_data error"))
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base cp own_data ok"))

        ### rsync own_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try cp own_conf"))
            if (newconfip != "" and newconfuser != "" and newconfpassw != "" and newconfpath != ""):
                ret = cp_own_env(base_path, newconfip, newconfuser, newconfpassw, newconfpath, type_2)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            update_errorlog("[%s] %s\n" % (get_now_time(), "base cp own_conf error"))
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base cp own_conf ok"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "base env build ok"))
        
        ### start perform
        if (testitem == 1):#need to run performance
            try:
                ret = run_performace(base_path, "cost_base")
                if (ret != 0):
                    set_status(3)
                    return -1
            except Exception, e:
                update_errorlog("[%s] %s\n" % (get_now_time(), e))
                set_status(3)
                return -1
            if (ret != 0):
                set_status(3)
                return 5
        set_status(4)


##### run test & run base

    if just_run_test == 0 and just_run_base == 0:

        update_errorlog("[%s] %s\n" % (get_now_time(), "try start test and base"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build test enviroment"))
        ### check test code
        try:
            print "testsvn", testsvn
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try check code"))
            ret = checkcode_env(test_path, testsvn)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test check code ok"))
        
        ### test make
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try make"))
            ret = make_env(test_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test make ok"))
        
        ### test rsync ol_data && ol_dev_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp ol_data and ol_dev_conf"))
            ret = cp_ol_env(ol_data_path, test_path, ol_conf_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp ol_data and ol_dev_conf ok"))

        ### test rsync press_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp press_conf"))
            ret = cp_press_conf_env(test_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp press_conf ok"))

        ### rsync own_data to test
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp own_data"))
            if (newdataip != "" and newdatauser != "" and newdatapassw != "" and newdatapath != ""):
                ret = cp_own_env(test_path, newdataip, newdatauser, newdatapassw, newdatapath, type_1)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_data error"))
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_data ok"))

        ### rsync own_conf to test
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try cp own_conf"))
            if (newconfip != "" and newconfuser != "" and newconfpassw != "" and newconfpath != ""):
                ret = cp_own_env(test_path, newconfip, newconfuser, newconfpassw, newconfpath, type_2)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_conf error"))
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test cp own_conf ok"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "test env build ok"))
 



 ######### 
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build base enviroment"))
        ### check code
        try:
            print "basesvn", basesvn
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try check code"))
            ret = checkcode_env(base_path, basesvn)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base check code ok"))
        
        ### make
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try make"))
            ret = make_env(base_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base make ok"))
        
        ### rsync ol_data && ol_dev_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try cp ol_data and ol_dev_conf"))
            ret = cp_ol_env(ol_data_path, base_path, ol_conf_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base cp ol_data and ol_dev_conf ok"))

        ### rsync press_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try cp press_conf"))
            ret = cp_press_conf_env(base_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base env build ok"))

 ########


        ### start perform
        if (testitem == 1):#need to run performance
            try:
                ret = run_performace(test_path, "cost_test")
                if (ret != 0):
                    set_status(3)
                    return -1
            except Exception, e:
                update_errorlog("[%s] %s\n" % (get_now_time(), e))
                set_status(3)
                return -1
            if (ret != 0):
                set_status(3)
                return 5

            try:
                ret = run_performace(base_path, "cost_base")
                if (ret != 0):
                    set_status(3)
                    return -1
            except Exception, e:
                update_errorlog("[%s] %s\n" % (get_now_time(), e))
                set_status(3)
                return -1
            if (ret != 0):
                set_status(3)
                return 5


        set_status(4)
        return 0



######

def sig_handler(sig, frame):
    update_errorlog("[%s] task %d has been canceled\n" % (get_now_time(), mission_id))
    set_status(5)
    sys.exit()




signal.signal(10, sig_handler)
signal.signal(15, sig_handler)




if __name__ == '__main__':
    print main()
    #sync_ol_conf_to_local(sys.argv[2])
    #test()
