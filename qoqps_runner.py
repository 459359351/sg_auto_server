#! /usr/bin/env python
#coding=utf-8

import os
import sys
import pymysql
import time
import subprocess

from conf import *
from lib import logUtils
from lib import confhelper
from lib import asycommands
from lib import svnpkg
from lib import makelink

import psutil
import hashlib
import signal
import pexpect
import shutil
import urllib


db = pymysql.connect(database_host,database_user,database_pass,database_data)
cursor = db.cursor()

mission_id = int(sys.argv[1])
asycmd_list = list()
proc_list = list()
def get_now_time():
    timeArray = time.localtime()
    return  time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

def get_material():

#newconfpath | newconfip | newconfpassw | newconfuser | newdataip | newdatapassw | newdatauser | newdatapath | newdata_topath

    sql = "SELECT testsvn, basesvn, testitem, newconfip, newconfuser, newconfpassw, newconfpath, newdataip, newdatauser, newdatapassw, newdatapath, newdata_topath, press_qps, press_time, press_expid, press_rate FROM %s where id='%d'" % (database_table,mission_id)
    cursor.execute(sql)
    data = cursor.fetchone()
    sql = "UPDATE %s set start_time='%s', status = 2 where id=%d" % (database_table, get_now_time() ,mission_id)
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        pass
    #print("data", data)
    return data

def update_errorlog(log):
    logstr = logUtils.logutil(mission_id)
    #print(log.replace('\n', ''))
    log = log.replace("'", "\\'")
    sql = "UPDATE %s set errorlog=CONCAT(errorlog, '%s') where id=%d;" % (database_table, log, mission_id)
    cursor.execute(sql)
    data = cursor.fetchone()
    logstr.log_info(str(mission_id)+"\t"+log)
    try:
        db.commit()
    except:
        logstr.log_debug("error")
    return data


def set_status(stat):
    sql = "UPDATE %s set status=%d, end_time='%s' where id=%d" % (database_table, stat, get_now_time(), mission_id)
    cursor.execute(sql)
    db.commit()
    if (stat != 1):
        clean_proc()

def clean_proc():
    os.popen('killall -9 lt-queryoptimiz sggp')
    for pid in proc_list:
        try:
            stop_proc(pid)
        except:
            pass
    for asy in asycmd_list:
        try:
            asy.stop()
        except:
            pass
    time.sleep(3)

    return


def sync_ol_data_to_local(data_path):
    if os.path.exists(data_path) == False:
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
    asycmd = asycommands.TrAsyCommands(timeout=30*300)
    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', arg, arg2], shell=False):
        if (iotype is 1):
            stdlog += line.encode('utf-8') + '\n'
        elif (iotype is 2):
            errlog += line + '\n'
    if (asycmd.return_code() != 0):
        update_errorlog("[%s] rsync ol_data to local Error\n" % get_now_time())
        update_errorlog(errlog)
        return 1
    update_errorlog("[%s] rsync ol_data to local success\n" % get_now_time())
    return 0

def sync_olbl_data_to_local(data_path):
    arg = "%s::%s" % (online_host, data_path[1:])
    stdlog = ""
    errlog = ""
    asycmd = asycommands.TrAsyCommands(timeout=30*30)
    for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', arg, data_path], shell=False):
        if (iotype is 1):
            stdlog += line.encode('utf-8') + '\n'
        elif (iotype is 2):
            errlog += line + '\n'
    if (asycmd.return_code() != 0):
        update_errorlog("[%s] rsync olbl_data to local Error\n" % get_now_time())
        update_errorlog(errlog)
        return 1
    update_errorlog("[%s] rsync olbl_data to local success\n" % get_now_time())
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
    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', arg, arg2], shell=False):
        if (iotype is 1):
            stdlog += line + '\n'
        elif (iotype is 2):
            errlog += line + '\n'
    if (asycmd.return_code() != 0):
        update_errorlog("[%s] rsync ol_conf to local Error\n" % get_now_time())
        update_errorlog(errlog)
        return 1
    update_errorlog("[%s] rsync ol_conf to local success\n" % get_now_time())
    return 0




def checkcode_env(file_path, svn):
    if os.path.exists(file_path):
        update_errorlog("[%s] %s%s\n" % (get_now_time(), file_path, " dir exists, remkdir -p"))
        os.popen("rm -rf "+file_path)
        os.popen("mkdir -p " + file_path)

    update_errorlog("[%s] start check code [%s]\n" %(get_now_time(), file_path))
    
    mysvn = svnpkg.SvnPackage("qa_svnreader", "New$oGou4U!")

    for line in svn.split("\n"):
        pos = line.find('=')
        key = line[0:pos]
        value = line[pos+1:]
        if (value.find('http://') != 0):
            update_errorlog("[%s] svn url format error: %s\n" % (get_now_time(), line))
            return -1
        key_path = os.path.join(file_path, key)
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


def make_env(file_path):
    asycmd = asycommands.TrAsyCommands(timeout=1200)
    asycmd_list.append(asycmd)
    make_log = ""
    for iotype, line in asycmd.execute_with_data(['make', '-j8'], shell=False, cwd = file_path):
        if iotype is 2:
            make_log += line + "\n"
    if (asycmd.return_code() != 0):#timeout or error, then try again
        make_log = ""
        for iotype, line in asycmd.execute_with_data(['make' '-j8'], shell=False, cwd = file_path):
            if iotype is 2:
                make_log += line
    if (asycmd.return_code() != 0):
        update_errorlog(make_log)
        return 2
    update_errorlog("[%s] make success\n" % get_now_time())
    return 0


def maketestlink(oldata_local_path,tdata_path,newdata_path):
    new_data_lst = newdata_path.split('\n')
    new_data_dir = dict()
    for new_data in new_data_lst:
        new_data_dir[new_data.split(';')[0]]=new_data.split(';')[1]
    mklink = makelink.MakeLink(oldata_local_path,tdata_path,**new_data_dir)
    mklink.makelink()
    return 0


def scpnewdata(file_path,host_ip,username,password,newdata_path):
    new_data = newdata_path.split('\n')
    new_data_lst = list()
    for nd in new_data:
        if nd !="":
            new_data_lst.append(nd)
    # scp whole data to test
    if len(new_data_lst) == 1 and new_data_lst[0].split(';')[1]=='data':
        rd_path = new_data_lst[0].split(';')[0]
        if os.path.exists(file_path+'/data'):
            os.popen("rm -rf %s" % (file_path+'/data'))
            os.popen("mkdir -p %s" % (file_path+'/data'))
        arg = "%s::%s" % (host_ip, rd_path[1:]+'/')
        arg2 = file_path+'/data/'
        stdlog = ""
        errlog = ""
        #arg = 'rsync.webqo01.web.1.djt.ted::search/odin/daemon/qo/data/'
        #arg2 = '/search/summary_o/webqo/data/'
        asycmd = asycommands.TrAsyCommands(timeout=30*300)
        for iotype, line in asycmd.execute_with_data(['rsync', '-ravl', arg, arg2], shell=False):
            if (iotype is 1):
                stdlog += line.encode('utf-8') + '\n'
            elif (iotype is 2):
                errlog += line + '\n'
        if (asycmd.return_code() != 0):
            update_errorlog("[%s] rsync ol_data to local Error\n" % get_now_time())
            update_errorlog(errlog)
            return 1
        update_errorlog("[%s] rsync ol_data to local success\n" % get_now_time())
    else:
        new_data_dir = dict()
        for new_data in new_data_lst:
            new_data_dir[new_data.split(';')[0]]=new_data.split(';')[1]
        for item in new_data_dir:
            files = os.path.split(item)[1]
            if "{" in files:
                filename_lst = files[1:-1].split(',')
                for filename in filename_lst:
                    if os.path.exists(file_path+'/'+new_data_dir[item]+'/'+filename):
                        os.popen("rm -rf %s" % (file_path+'/'+new_data_dir[item]+'/'+filename))
            else:
                if os.path.exists(file_path+'/'+new_data_dir[item]+'/'+files):
                    os.popen("rm -rf %s" % (file_path+'/'+new_data_dir[item]+'/'+files))
 
            update_errorlog("[%s] try scp rd data %s to test enviroment\n" % (get_now_time(),new_data_dir[item]))

            passwd_key = '.*assword.*'

            cmdline = 'scp -r %s@%s:%s %s/' %(username, host_ip, item, file_path+'/'+new_data_dir[item])

            try:
                child=pexpect.spawn(cmdline)
                expect_result = child.expect([r'assword:',r'yes/no'],timeout=30)
                if expect_result == 0:
                    child.sendline(password)

                elif expect_result ==1:
                    child.sendline('yes')
                    child.expect(passwd_key,timeout=30)
                    child.sendline(password)
                child.timeout=120
                child.expect(pexpect.EOF)

            except Exception as e:
                update_errorlog("[%s] %s, scp rd data \n" % (get_now_time(), e))
            update_errorlog("[%s] try scp rd data %s  to test enviroment ok\n" % (get_now_time(),new_data_dir[item]))
    return 0


def cp_new_conf(tmp_conf_path, test_env_path):
    ### cp ol_dev_conf to test env
    update_errorlog("[%s] use cfg online ,cp it from tmp_conf_path\n" % get_now_time())
    if os.path.exists(test_env_path + "/QueryOptimizer/qo.cfg"):
        update_errorlog("[%s] %s\n" % (get_now_time(), "cfg  exists, del it"))
        os.popen("rm -rf " + test_env_path + "/QueryOptimizer/qo.cfg")

    os.popen("cp %s/qo.cfg %s/QueryOptimizer/" % (tmp_conf_path, test_env_path))
    update_errorlog("[%s] cp cfg from tmp_conf_path success\n" % get_now_time())

    return 0

def cp_start_sc(file_path):
    update_errorlog("[%s] %s\n" % (get_now_time(), "cp start.sh to env"))
    if os.path.exists(file_path + "/QueryOptimizer/start.sh"):
        update_errorlog("[%s] %s\n" % (get_now_time(), "test start.sh is exists, del it"))
        os.popen("rm -rf " + file_path + "/QueryOptimizer/start.sh")
    os.popen("cp %s  %s/QueryOptimizer/" % (start_sc, file_path))
    update_errorlog("[%s] %s\n" % (get_now_time(), "cp start.sh to env success"))
    return 0


def scp_new_conf(file_path,newconfip,newconfuser,newconfpassw,newconfpath):
    update_errorlog("[%s] try scp rd qo.cfg to test enviroment\n" % get_now_time())
    if os.path.exists(file_path + "/QueryOptimizer/qo.cfg"):
        update_errorlog("[%s] %s\n" % (get_now_time(), "cfg  exists, del it"))
        os.popen("rm -rf " + file_path + "/QueryOptimizer/qo.cfg")

    passwd_key = '.*assword.*'

    cmdline = 'scp -r %s@%s:%s %s/' %(newconfuser, newconfip, newconfpath, file_path+'/QueryOptimizer')
    try:
        child=pexpect.spawn(cmdline)
        expect_result = child.expect([r'assword:',r'yes/no'],timeout=30)
        if expect_result == 0:
            child.sendline(newconfpassw)
        elif expect_result ==1:
            child.sendline('yes')
            child.expect(passwd_key,timeout=30)
            child.sendline(newconfpassw)
        child.expect(pexpect.EOF)

    except Exception as e:
        update_errorlog("[%s] %s, scp rd qo.cfg failed \n" % (get_now_time(), e))
    update_errorlog("[%s] try scp rd qo.cfg to test enviroment success\n" % get_now_time())
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
#        print("[%s] proc_status: %s" %(get_now_time(), get_proc_status(pid)))
        time.sleep(interval)
#        print("[%s] sleep_interval: %s" %(get_now_time(), interval))
        if (interval > 10):
            interval = interval/2


def stop_proc(pid):
    os.popen("/bin/kill -9 %d" % pid)
    wait_to_die(pid, 2)
    return 0


def lanch(file_path, start_script, port, log):
# rules: start_script must put pid in `PID` file: echo $! > PID
# return a tuple(retcode, pid)
#lanch(sggp_path, "start_qo_group.sh", -1, log)
    pid = -1
    asycmd = asycommands.TrAsyCommands(timeout=30)
    asycmd_list.append(asycmd)
    child = subprocess.Popen(['/bin/sh', start_script], shell=False, cwd = file_path, stderr = subprocess.PIPE)
    child.wait()
    if (child.returncode != 0):
        log.append(child.stderr.read())
        return (-1, pid)
    for iotype, line in asycmd.execute_with_data(['/bin/cat', file_path + "/PID"], shell=False):
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
    proc_list.append(pid)
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
        proc_list.remove(pid)
        return (-3, pid)
    return (start_time, pid)



def run_performace(file_path, cost_type):
    cost = []
    ret = performance_once(file_path, cost, cost_type)
    if (ret !=0):
        return ret
    set_content_to_x(cost, cost_type)
    return 0


def set_content_to_x(content, cost_type):
    tmp = []
    total_content = ""
    if (type(content) == type(tmp)):
        for line in content:
            total_content += line + '\n'
    elif (type(content) == type(total_content)):
        total_content = content
    sql = "UPDATE %s set %s='%s' where id=%d" % (database_table, cost_type, total_content.decode('gbk').encode('utf8'), mission_id)
    cursor.execute(sql)
    db.commit()


def performance_once(file_path, performance_result, cost_type):
    asycmd = asycommands.TrAsyCommands(timeout=120)
    asycmd_list.append(asycmd)

    # kill lt-queryoptimiz
    for iotype, line in asycmd.execute_with_data(['ps -ef|grep lt-queryoptimiz|grep -v grep'], shell=True):
        if (line.find('lt-queryoptimiz') != -1):
            pid = int(line.split()[1])
            stop_proc(pid)

    log = []
    # start lt-queryoptimiz
    update_errorlog("[%s] Begin Start %s webqo\n" % (get_now_time(),cost_type))
    (ret, cache_pid) = lanch(file_path + "/QueryOptimizer", "start.sh", 8012, log)
    if (ret < 0):
        time.sleep(0.5)
        up_log = ""
        for line in log:
            up_log += "[%s] %s" % (get_now_time(), line + '\n')
        update_errorlog("%s\n" % (up_log))
        for iotype, line in asycmd.execute_with_data(['/bin/tail', '-50', file_path + "/QueryOptimizer/err.log"], shell=False):
            up_log += line +'\n'
        update_errorlog(up_log.decode('gbk').encode('utf-8').replace("'", "\\'"))
        return -1
    update_errorlog("[%s] %s webqo Start OK, cost %d s\n" % (get_now_time(), cost_type, ret))

    # Start PressTool
    log = []
    update_errorlog("[%s] Begin start PressTool\n" % get_now_time())
    if cost_type == 'cost_test':
        (ret, tools_pid) = sggp_lanch(sggp_path, "start_qo_test.sh", log)
    else:
        (ret, tools_pid) = sggp_lanch(sggp_path, "start_qo_base.sh", log)
    print ret,tools_pid
    if (ret < 0):
        time.sleep(0.5)
        up_log = ""
        for line in log:
            up_log += "[%s] %s" % (get_now_time(), line + '\n')
        update_errorlog("%s\n" % (up_log))
        up_log = ""
        for iotype, line in asycmd.execute_with_data(['/bin/tail', '-50', sggp_path + "/err"], shell=False):
            up_log += line + '\n'
        update_errorlog(up_log.decode('gbk').encode('utf-8').replace("'", "\\'"))
        return -1
    update_errorlog("[%s] PressTool Start OK\n" % get_now_time())
    update_errorlog("[%s] Wait PressTool...\n" % get_now_time())

    # Wait PressTool Stop
    for subpid in tools_pid:
        wait_to_die(subpid, 5*30)
    update_errorlog("[%s] PressTool stoped\n" % get_now_time())

    # Stop webqo
    stop_proc(cache_pid)
    update_errorlog("[%s] %s webqo stoped\n" % (get_now_time(),cost_type))

    return get_performance(file_path + '/QueryOptimizer/err.log', performance_result)

def get_performance(log_file, performance):
    update_errorlog("[%s] start to get performance result\n" % get_now_time())
    if (os.path.exists(log_file) is False):
        performance.append(log_file + " is not exists")
        return -1

    asycmd = asycommands.TrAsyCommands(timeout=240)
    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['python', cost_tool, log_file], shell=False):
        performance.append(line)
    if (asycmd.return_code() != 0):
        return asycmd.return_code()
    return 0

def sggp_lanch(file_path, start_script, log):
# rules: start_script must put pid in `PID` file: echo $! > PID
# return a tuple(retcode, pid)
#lanch(sggp_path, "start_qo_group.sh", -1, log)
    pid = list()
    asycmd = asycommands.TrAsyCommands(timeout=30)
    asycmd_list.append(asycmd)
    child = subprocess.Popen(['/bin/sh', start_script], shell=False, cwd = file_path, stdout = subprocess.PIPE,stderr = subprocess.PIPE)
    child.wait()
    if (child.returncode != 0):
        log.append(child.stderr.read())
        return (-1, pid)
    for iotype, line in asycmd.execute_with_data(['/bin/cat', file_path + "/PID"], shell=False):
        if (iotype == 1 and line != ""):
            try:
                pid.append(int(line))
            except:
                continue
    if len(pid) == 0:
        return (-2, pid)
    proc = None
    for subpid in pid:
        try:
            proc = psutil.Process(subpid)
        except:
            log.append("process %d is not alive" % pid)
            return (-3, pid)
    return (0, pid)


def configure_sggp(sggp_conf_file,qps,time):
    if qps == '':
        qps = 1000
    if time == '' or time > 30:
        time = 15

    os.popen("sed -i 's/press_time=.*/press_time=%s/g' %s" %(time, sggp_conf_file))
    os.popen("sed -i 's/press_qps=.*/press_qps=%s/g' %s" %(qps, sggp_conf_file))
    update_errorlog("[%s] configure sggp_conf success\n" % get_now_time())
    
    return 0

def configure_sggp_test(sggp_path,qps,time,press_expid,press_rate):
    if qps == '':
        qps = 1000
    if time == '' or time > 30:
        time = 15
    cfg_expall = confhelper.ConfReader(sggp_path+'/web_qo_expall.ini')
    cfg_expall.setValue('web_qo_exp','press_qps',qps)
    cfg_expall.setValue('web_qo_exp','press_time',time)
    
    cfg_online = confhelper.ConfReader(sggp_path+'/web_qo_online.ini')
    cfg_online.setValue('web_qo','press_qps',qps)
    cfg_online.setValue('web_qo','press_time',time)

    if(os.path.exists(sggp_path+'/start_qo_test.sh')):
        print 'start_qo_test is exist,del it'
        update_errorlog("[%s] start_qo_test is exist,del it\n" % get_now_time())
        os.popen('rm -rf %s' % (sggp_path+'/start_qo_test.sh'))
    if press_expid != 0 and press_rate > 0:
        print sggp_path,qps,press_expid,press_rate
        expid= hex(press_expid)[2:]+'^0^0^0^0^0^0^0^0'
        commandline = 'echo '+expid+' | /search/odin/daemon/webqo/tools/sggp/data/Encode -f utf8 -t utf16'
        asycmd = asycommands.TrAsyCommands(timeout=240)
        asycmd_list.append(asycmd)
        for iotype, line in asycmd.execute_with_data([commandline], shell=True):
            exp_id = "exp_id="+line
        base_query=sggp_query_path+'query_qo_base'
        command = '''awk '{print "'''+exp_id+""""$0}' """ +base_query+">"+sggp_query_path+"query_qo_expid"
        try:
            child = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            child.communicate(input=None)
            child.poll()
        except Exception as e:
            update_errorlog("[%s] create expid query wrong ,except:%s\n" % (get_now_time(), e))
        if press_rate < 100:
            qo_expid_qps=qps*press_rate/100
            qo_qps = 1000-qo_expid_qps
            cfg=confhelper.ConfReader(sggp_path+'/web_qo_group.ini')
            cfg.setValue('web_qo_exp','press_qps',int(qo_expid_qps))
            cfg.setValue('web_qo','press_qps',int(qo_qps))
            cfg.setValue('web_qo_exp','press_time',time)
            cfg.setValue('web_qo','press_time',time)
            os.symlink(sggp_path+'/start_qo_group.sh',sggp_path+'/start_qo_test.sh')
        elif press_rate == 100:
            os.symlink(sggp_path+'/start_qo_expall.sh',sggp_path+'/start_qo_test.sh')
    else:
        os.symlink(sggp_path+'/start_qo_online.sh',sggp_path+'/start_qo_test.sh')
    return 0    


def main():
    loginfo = logUtils.logutil(mission_id) 
    test_path = root_path + test_path_1
    base_path = root_path + base_path_1

    ol_data_path = ol_data_path_1
    ol_conf_path = root_path + ol_conf_path_1

    loginfo.log_info("test_path:"+test_path)
    loginfo.log_info("base_path:"+base_path)

    loginfo.log_info("ol_data_path:"+ol_data_path)
    loginfo.log_info("ol_conf_path:"+ol_conf_path)

    loginfo.log_info("mission_id:"+str(mission_id))

    (testsvn, basesvn, testitem, newconfip, newconfuser, newconfpassw,newconfpath, newdataip, newdatauser, newdatapassw, newdatapath, newdata_topath, press_qps, press_time, press_expid, press_rate) = get_material()
    
    loginfo.log_info("testsvn:"+ testsvn)
    loginfo.log_info("basesvn:"+basesvn)
    loginfo.log_info("testitem:"+str(testitem))
    loginfo.log_info("newconfip:"+ newconfip)
    loginfo.log_info("newconfuser:"+ newconfuser)
    loginfo.log_info("newconfpassw:"+ newconfpassw)
    loginfo.log_info("newconfpath:"+ newconfpath)
    loginfo.log_info("newdataip:"+ newdataip)
    loginfo.log_info("newdatauser:"+ newdatauser)
    loginfo.log_info("newdatapassw:"+ newdatapassw)
    loginfo.log_info("newdatapath:"+ newdatapath)
    loginfo.log_info("newdata_topath:"+newdata_topath)
    loginfo.log_info("press_qps:"+str(press_qps))
    loginfo.log_info("press_time:"+str(press_time))
    loginfo.log_info("press_expid:"+str(press_expid))
    loginfo.log_info("press_rate:"+str(press_rate))

    ####configure sggp/ACE_Pressure_CACHE.ini

#    ret_configure_sggp = configure_sggp(sggp_conf,press_qps,press_time)
#    if ret_configure_sggp != 0:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "configure sggp_conf has some error, pls check"))
#        set_status(3)
#        return -1

    ret_configure_sggp_test = configure_sggp_test(sggp_path,press_qps,press_time,press_expid,press_rate)
    if ret_configure_sggp_test != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "configure sggp_conf has some error, pls check"))
        set_status(3)
        return -1
    
#    ret_sync_ol_data = sync_ol_data_to_local(ol_data_path+"/data")
#    if ret_sync_ol_data != 0:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_ol_data_to_local has some error, pls check"))
#        set_status(3)
#        return -1

    ret_sync_olbl_data = sync_olbl_data_to_local(black_data_path)
    if ret_sync_olbl_data != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_olbl_data_to_local has some error, pls check"))
        set_status(3)
        return -1

    ret_sync_ol_conf = sync_ol_conf_to_local(ol_conf_path)
    if ret_sync_ol_conf != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_ol_conf_to_local has some error, pls check"))
        set_status(3)
        return -1



#### just run test
    if testsvn.strip() !="":        
        update_errorlog("[%s] %s\n" % (get_now_time(), "try start test"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build test enviroment"))

        ### check code
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try check code"))
            ret = checkcode_env(test_path, testsvn)
        except Exception as e:
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
        except Exception as e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test make ok"))
        
        
        ### make test data link and scp new data to test env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try to make link with ol_data on test"))
            if newdatapath == '':
                if(os.path.exists(test_path+'/QueryOptimizer/data')):
                    loginfo.log_info('test_path_data_dir is exist')
                    os.popen('rm -rf %s' % (test_path+'/QueryOptimizer/data'))
                os.symlink(ol_data_path+'/data',test_path+'/QueryOptimizer/data')
            else:
                res = maketestlink(ol_data_path,test_path+'/QueryOptimizer',newdatapath)
                if (res != 0):
                    set_status(3)
                    return 4
                if ";" in newdatapath and newdataip!='' and newdatauser!='' and newdatapassw!='':
                    scpres = scpnewdata(test_path+'/QueryOptimizer',newdataip,newdatauser,newdatapassw,newdatapath)
                else:
                    scpres = 1
                    update_errorlog("[%s] %s\n" % (get_now_time(), "test new data configure is wrong"))
                if (scpres != 0):
                    set_status(3)
                    return 4
        except Exception as e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1
        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try to make link with ol_data on test ok"))



        ### scp new conf to test env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start to ctrl cfg "))
            if newconfpath == '': 
                loginfo.log_info('use cfg online')
                ret = cp_new_conf(ol_conf_path,test_path)
            elif newconfip!='' and newconfuser!='' and newconfpassw!='':
                loginfo.log_info('use rd cfg')
                ret = scp_new_conf(test_path,newconfip,newconfuser,newconfpassw,newconfpath)
            else:
                ret = 1
                update_errorlog("[%s] %s\n" % (get_now_time(), "test new conf configure is wrong"))
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test start to cp ol_data and ol_dev_conf ok"))
        


        ### cp start.sh to env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start to cp start.sh to test env"))
            ret = cp_start_sc(test_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "test  cp start.sh to test env ok")) 


        
#        ### start perform
#        if (testitem == 1):#need to run performance
#            try:
#                ret = run_performace(test_path, "cost_test")
#                if (ret != 0):
#                    set_status(3)
#                    return -1
#            except Exception as e:
#                update_errorlog("[%s] %s\n" % (get_now_time(), e))
#                set_status(3)
#                return -1
#            if (ret != 0):
#                set_status(3)
#                return 5


###### just run base
    if basesvn.strip() !="":

        update_errorlog("[%s] %s\n" % (get_now_time(), "try start base"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build base enviroment"))
        ### check code
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try check code"))
            ret = checkcode_env(base_path, basesvn)
        except Exception as e:
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
        except Exception as e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "base make ok"))
       
        ### make base data link 
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "start try to make link with ol_data on base"))
            if(os.path.exists(base_path+'/QueryOptimizer/data')):
                loginfo.log_info('base_path_data_dir is exist')
                os.popen('rm -rf %s' % (base_path+'/QueryOptimizer/data'))
            os.symlink(ol_data_path+'/data',base_path+'/QueryOptimizer/data')
        except Exception as e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try to make link with ol_data on base ok"))

        ### cp conf to base env from tem_conf
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "cp cfg to base from tem_conf"))
            ret = cp_new_conf(ol_conf_path,base_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "cp cfg to base from tem_conf ok"))

        ### cp start.sh to env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "start to cp start.sh to base env"))
            ret = cp_start_sc(base_path)
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "cp start.sh to base env ok")) 

    if testsvn.strip() !="":
        ### start test perform
        if (testitem == 1):
            try:
                ret = run_performace(test_path, "cost_test")
                if (ret != 0):
                    set_status(3)
                    return -1
            except Exception as e:
                update_errorlog("[%s] %s\n" % (get_now_time(), e))
                set_status(3)
                return -1
            if (ret != 0):
                set_status(3)
                return 5
    if basesvn.strip() !="":
        ### start base perform
        if (testitem == 1):
            try:
                ret = run_performace(base_path, "cost_base")
                if (ret != 0):
                    set_status(3)
                    return -1
            except Exception as e:
                update_errorlog("[%s] %s\n" % (get_now_time(), e))
                set_status(3)
                return -1
            if (ret != 0):
                set_status(3)
                return 5
    set_status(4)
    return 0




def sig_handler(sig, frame):
    update_errorlog("[%s] task %d has been canceled\n" % (get_now_time(), mission_id))
    set_status(5)
    sys.exit()




signal.signal(10, sig_handler)
signal.signal(15, sig_handler)




if __name__ == '__main__':
    main()
