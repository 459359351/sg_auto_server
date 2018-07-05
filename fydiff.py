#! /usr/bin/env python
#coding=utf-8

import os
import sys
import pymysql
import time
import subprocess

from fyconf import *
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
hub_svn_base = ''
server_svn_base=''
def get_now_time():
    timeArray = time.localtime()
    return  time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

def get_material():

#newconfpath | newconfip | newconfpassw | newconfuser | newdataip | newdatapassw | newdatauser | newdatapath | newdata_topath

    sql = "SELECT hubcfgip,hubcfguser,hubcfgpassw,hubcfgpath,hubdatapath,sercfgip,sercfguser,sercfgpassw,sercfgpath,serdatapath,queryip,queyruser,querypassw,querypath,hubsvn,sersvn FROM %s where id='%d'" % (database_table,mission_id)
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


def sync_ol_data_to_local(local_path,data_type):
    if os.path.exists(local_path) == False:
        update_errorlog("[%s] %s\n" % (get_now_time(), "tmp_ol_data path not exists, mkdir -p")) 
        os.popen("mkdir -p " + local_path)

    update_errorlog("[%s] start rsync online %s to local\n" % (get_now_time(),data_type))

    if data_type == 'hub_data':
        online_host = online_host_hub
        rsync_path = online_path_hub + '/data'
    elif data_type == 'hub_conf':
        online_host = online_host_hub
        rsync_path = online_path_hub + '/conf'
    elif data_type == 'server_data':
        online_host = online_host_server
        rsync_path = online_path_server + '/data'
    elif data_type == 'server_conf':
        online_host = online_host_server
        rsync_path = online_path_server + '/conf'
    elif data_type == 'hub_agent':
        online_host = online_host_hub
        rsync_path = hub_data_agent
    elif data_type == 'server_agent':
        online_host = online_host_server
        rsync_path = server_data_agent
    elif data_type == 'hub_info':
        online_host = online_host_hub
        rsync_path = online_path_hub + '/info'
    elif data_type == 'server_info':
        online_host = online_host_server
        rsync_path = online_path_server + '/info'
    else:
        update_errorlog("[%s] rsync data_type error  %s \n" % (get_now_time(),data_type))
        return 1
        rsync_path = data_agent
    if (rsync_path[0:1] == "/"):
        rsync_path = rsync_path[1:]
    if (rsync_path[-1] != "/"):
        rsync_path = rsync_path + "/"
    rsync_path = rsync_path
    arg2 = local_path
    if (local_path[-1] != "/"):
        arg2 = local_path + "/"

    arg = "%s::%s" % (online_host, rsync_path)
    print(arg,local_path)
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
        update_errorlog("[%s] rsync online %s to local Error\n" % (get_now_time(),data_type))
        update_errorlog(errlog)
        return 1
    update_errorlog("[%s] rsync online %s to local success\n" % (get_now_time(),data_type))
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
        if line.strip() == '':
            continue
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


#cp_cfg(ol_conf_hub,test_hub+'/server_frame/conf')
def cp_cfg(ol_conf_hub,dist_path):
    ### cp online cfg to test env
    update_errorlog("[%s] use cfg online ,cp it from %s \n" % (get_now_time(),ol_conf_hub))
    if os.path.exists(dist_path):
        update_errorlog("[%s] cfg dir %s is exists,del it\n" % (get_now_time(), dist_path))
        os.popen("rm -rf " + dist_path)
        os.popen("mkdir -p " + dist_path)
    os.popen("cp -r %s/* %s/" % (ol_conf_hub, dist_path))
    return 0


def modify_hub_cfg(cfg_path,hub_port,server_fst,server_sec):
    try:
        os.popen("sed -i -e '/ywserver0[3-9].fy.sjs.ted/d' %s" %( cfg_path+'/backend.cfg'))
        os.popen("sed -i -e '/ywserver1[0-9].fy.sjs.ted/d' %s" %( cfg_path+'/backend.cfg'))
        os.popen("sed -i -e 's/server_name:.*ywserver01.fy.sjs.ted.*18000/server_name:\"10.153.51.61\" port:%s/' %s" %(server_fst,cfg_path+'/backend.cfg'))
        os.popen("sed -i -e 's/server_name:.*ywserver02.fy.sjs.ted.*18000/server_name:\"10.153.51.61\" port:%s/' %s" %(server_sec,cfg_path+'/backend.cfg'))
        os.popen("sed -i -e 's/listen_port:.*/listen_port:%s/' %s" %(hub_port,cfg_path+'/uniq_trans_hub1.cfg'))
    except Exception as e:
        update_errorlog("[%s] %s, sed cfg failed \n" % (get_now_time(), e))
        return 2
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
    os.popen("cp %s  %s/" % (start_sc_test, file_path))
    update_errorlog("[%s] %s\n" % (get_now_time(), "cp start.sh to env success"))
    return 0


def scp_new_file(file_path,newfileip,newfileuser,newfilepassw,newfilepath,filetype):
    update_errorlog("[%s] try scp rd %s to test enviroment\n" % (get_now_time(),filetype))
    if os.path.exists(file_path):
        update_errorlog("[%s] %s dir exists,del it\n" % (get_now_time(), filetype))
        os.popen("rm -rf " + file_path)

    passwd_key = '.*assword.*'

    cmdline = 'scp -r %s@%s:%s %s/' %(newfileuser, newfileip, newfilepath, file_path)
    try:
        child=pexpect.spawn(cmdline,maxread=20000,timeout=300)
        os.popen("set timeout -1")
        expect_result = child.expect([r'assword:',r'yes/no', pexpect.EOF, pexpect.TIMEOUT])
        if expect_result == 0:
            child.sendline(newfilepassw)
            os.popen("set timeout -1")
        elif expect_result ==1:
            child.sendline('yes')
            child.expect(passwd_key,timeout=30)
            child.sendline(newfilepassw)
        child.expect(pexpect.EOF)

    except Exception as e:
        update_errorlog("[%s] %s, scp rd %s failed \n" % (get_now_time(), e,filetype))
    update_errorlog("[%s] try scp rd %s to test enviroment success\n" % (get_now_time(),filetype))
    return 0


def get_proc_status(pid,file_path,cost_type):
    try:
        if file_path !="" and cost_type != "":
            for fname in os.listdir(file_path+'/QueryOptimizer'):
                if 'core' in fname:
                    corefile = runlogbak+cost_type+'_startcore_'+str(mission_id)
                    os.popen("cp %s %s" % (file_path+'/QueryOptimizer/core.*', corefile))
                    bakfile = runlogbak+cost_type+'_starterr_'+str(mission_id)
                    os.popen("cp %s %s" % (file_path+'/QueryOptimizer/err.log', bakfile))
                    update_errorlog("[%s] service core,core file path %s \n" % (get_now_time(),local_ip+runlogbak))
                    return -1
        p = psutil.Process(pid)
    except:
        return -1
    if (p.status() == "running"):
        return 0
    elif (p.status() == "sleeping"):
        return 1
    return 2



def wait_to_die(pid, interval,file_path="",cost_type=""):
    while get_proc_status(pid,file_path,cost_type) is not -1:
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

    # clean Mem
    sync_cmd = subprocess.Popen(['sync'], shell=False, cwd = file_path, stdout = subprocess.PIPE,stderr = subprocess.PIPE)
    sync_cmd.wait()
    if (sync_cmd.returncode == 0):
        update_errorlog("[%s] %s sync success \n" % (get_now_time(), cost_type))
    else:
        update_errorlog("[%s] %s sync error \n" % (get_now_time(), cost_type))

    echo_three_cmd = subprocess.Popen(['echo 3 > /proc/sys/vm/drop_caches'], shell=True, stdout = subprocess.PIPE,stderr = subprocess.PIPE)
    echo_three_cmd.wait()
    if (sync_cmd.returncode == 0):
        update_errorlog("[%s] %s free mem success \n" % (get_now_time(), cost_type))
    else:
        update_errorlog("[%s] %s free pagecache, dentries and inodes error \n" % (get_now_time(), cost_type))

    echo_one_cmd = subprocess.Popen(['echo 0 > /proc/sys/vm/drop_caches'], shell=True, stdout = subprocess.PIPE,stderr = subprocess.PIPE)
    echo_one_cmd.wait()
    if (sync_cmd.returncode == 0):
        update_errorlog("[%s] %s reset success \n" % (get_now_time(), cost_type))
    else:
        update_errorlog("[%s] %s reset free error \n" % (get_now_time(), cost_type))

    log = []
    # start lt-queryoptimiz
    update_errorlog("[%s] Begin Start %s webqo\n" % (get_now_time(),cost_type))
    (ret, service_pid) = lanch(file_path + "/QueryOptimizer", "start.sh", 8012, log)
    if (ret < 0):
        bakfile = runlogbak+cost_type+'_starterr_'+str(mission_id)
        os.popen("cp %s %s" % (file_path+'/QueryOptimizer/err.log', bakfile))
        update_errorlog("[%s] %s webqo Start error, errlog path %s s\n" % (get_now_time(), cost_type, local_ip+runlogbak))
        for fname in os.listdir(file_path+'/QueryOptimizer'):
            if 'core' in fname:
                corefile = runlogbak+cost_type+'_startcore_'+str(mission_id)
                os.popen("cp %s %s" % (file_path+'/QueryOptimizer/core.*', corefile))
                update_errorlog("[%s] %s webqo Start core, core file path %s s\n" % (get_now_time(), cost_type, local_ip+runlogbak))
        time.sleep(0.5)
        up_log = ""
        for line in log:
            up_log += "[%s] %s" % (get_now_time(), line + '\n')
        update_errorlog("%s\n" % (up_log))
        for iotype, line in asycmd.execute_with_data(['/bin/tail', '-50', file_path + "/QueryOptimizer/err.log"], shell=False):
            up_log += line +'\n'
        update_errorlog(up_log.decode('gbk').encode('utf-8').replace("'", "\\'"))
        return -1
    update_errorlog("[%s] %s webqo Start OK, cost %d s, PID %s \n" % (get_now_time(), cost_type, ret, str(service_pid)))

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
    update_errorlog("[%s] PressTool Start OK ,PIDs %s \n" % (get_now_time(),str(tools_pid)))
    update_errorlog("[%s] Wait PressTool...\n" % get_now_time())

    # Wait PressTool Stop
    for subpid in tools_pid:
        wait_to_die(subpid, 5*30,file_path,cost_type)
    update_errorlog("[%s] PressTool stoped\n" % get_now_time())

    # Stop webqo
    stop_proc(service_pid)
    update_errorlog("[%s] %s webqo stoped\n" % (get_now_time(),cost_type))

    return get_performance(file_path + '/QueryOptimizer/err.log', performance_result,cost_type)

def get_performance(log_file, performance,cost_type):
    update_errorlog("[%s] start to get performance result %s \n" % (get_now_time(),log_file))
    bakfile = runlogbak+cost_type+'_err_'+str(mission_id)
    os.popen("cp %s %s" % (log_file, bakfile))
    if (os.path.exists(log_file) is False):
        performance.append(log_file + " is not exists")
        return -1

    asycmd = asycommands.TrAsyCommands(timeout=240)
    asycmd_list.append(asycmd)
    for iotype, line in asycmd.execute_with_data(['python3', cost_tool, log_file], shell=False):
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
        time = 30
    thread_size = int(qps/4)
    cfg_expall = confhelper.ConfReader(sggp_path+'/web_qo_expall.ini')
    cfg_expall.setValue('web_qo_exp','press_qps',qps)
    cfg_expall.setValue('web_qo_exp','thread_size',thread_size)
    cfg_expall.setValue('web_qo_exp','press_time',time)
    
    cfg_online = confhelper.ConfReader(sggp_path+'/web_qo_online.ini')
    cfg_online.setValue('web_qo','press_qps',qps)
    cfg_online.setValue('web_qo','thread_size',thread_size)
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
            cfg.setValue('web_qo_exp','thread_size',int(qo_expid_qps))
            cfg.setValue('web_qo','press_qps',int(qo_qps))
            cfg.setValue('web_qo','thread_size',int(qo_qps/5))
            cfg.setValue('web_qo_exp','press_time',time)
            cfg.setValue('web_qo','press_time',time)
            os.symlink(sggp_path+'/start_qo_group.sh',sggp_path+'/start_qo_test.sh')
        elif press_rate == 100:
            os.symlink(sggp_path+'/start_qo_expall.sh',sggp_path+'/start_qo_test.sh')
    else:
        os.symlink(sggp_path+'/start_qo_online.sh',sggp_path+'/start_qo_test.sh')
    return 0    
def svninfo_from_job(job_ini_path,svn_type):
    global hub_svn_base
    global server_svn_base
    flag = False
    try:
        if os.path.exists(job_ini_path+'/job.ini'):
            with open(job_ini_path+'/job.ini','r') as svninfo:
                for line in svninfo.readlines():
                    line = line.strip()
                    if 'main.svn' in line:
                        flag = True
                        continue
                    if flag == True:
                        if svn_type == 'hub_job_svn':
                            hub_svn_base+=(line+'\n')
                        elif svn_type == 'server_job_svn':
                            server_svn_base+=(line+'\n') 
                        else:
                            update_errorlog("[%s] %s type is wrong \n" % (get_now_time(), svn_type))
                            return -1
        else:
            update_errorlog("[%s] %s job.ini is not exists \n" % (get_now_time(), svn_type))
            return -1
    except Exception as e:
        update_errorlog("[%s] read job.ini failed ,except:%s\n" % (get_now_time(), e))
        return -1
    return 0

def main():
    loginfo = logUtils.logutil(mission_id) 
    test_hub = root_path + test_hub_path
    base_hub = root_path + base_hub_path
    
    test_server = root_path + test_server_path
    base_server = root_path + base_server_path

    ol_data_hub = root_path + online_data_hub
    ol_data_server = root_path + online_data_server

    ol_conf_hub = root_path + online_conf_hub
    ol_conf_server = root_path + online_conf_server

    ol_info_hub = root_path + online_job_hub
    ol_info_server = root_path + online_job_server

    loginfo.log_info("test_hub:"+test_hub)
    loginfo.log_info("base_hub:"+base_hub)

    loginfo.log_info("test_server:"+test_server)
    loginfo.log_info("base_server:"+base_server)

    loginfo.log_info("ol_data_hub:"+ol_data_hub)
    loginfo.log_info("ol_data_server:"+ol_data_server)

    loginfo.log_info("ol_conf_hub:"+ ol_conf_hub)
    loginfo.log_info("ol_conf_server:"+ ol_conf_server)
    
    loginfo.log_info("ol_info_hub:"+ ol_info_hub)
    loginfo.log_info("ol_info_server:"+ ol_info_server)

    loginfo.log_info("mission_id:"+str(mission_id))

    (hubcfgip,hubcfguser,hubcfgpassw,hubcfgpath,hubdatapath,sercfgip,sercfguser,sercfgpassw,sercfgpath,serdatapath,queryip,queyruser,querypassw,querypath,hubsvn,sersvn) = get_material()

    loginfo.log_info("hub_svn:"+ hubsvn)
    loginfo.log_info("server_svn:"+ sersvn)
    loginfo.log_info("hubcfgip:"+ hubcfgip)
    loginfo.log_info("hubcfguser:"+ hubcfguser)
    loginfo.log_info("hubcfgpassw:"+ hubcfgpassw)
    loginfo.log_info("hubcfgpath:"+ hubcfgpath)
    loginfo.log_info("hubdatapath:"+ hubdatapath)
    loginfo.log_info("sercfgip:"+ sercfgip)
    loginfo.log_info("sercfguser:"+ sercfguser)
    loginfo.log_info("sercfgpassw:"+ sercfgpassw)
    loginfo.log_info("sercfgpath:"+ sercfgpath)
    loginfo.log_info("serdatapath:"+ serdatapath)
    loginfo.log_info("queryip:"+ queryip)
    loginfo.log_info("queyruser:"+ queyruser)
    loginfo.log_info("querypassw:"+ querypassw)
    loginfo.log_info("querypath:"+ querypath)

    ####configure sggp/ACE_Pressure_CACHE.ini

#    ret_configure_sggp = configure_sggp(sggp_conf,press_qps,press_time)
#    if ret_configure_sggp != 0:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "configure sggp_conf has some error, pls check"))
#        set_status(3)
#        return -1

#    ret_configure_sggp_test = configure_sggp_test(sggp_path,press_qps,press_time,press_expid,press_rate)
#    if ret_configure_sggp_test != 0:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "configure sggp_conf has some error, pls check"))
#        set_status(3)
#        return -1
    # rsync hub data from online to local    
    sync_ol_data_hub = sync_ol_data_to_local(ol_data_hub,'hub_data')
    if sync_ol_data_hub != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_hub_data_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync hub conf from online to local
    sync_ol_conf_hub = sync_ol_data_to_local(ol_conf_hub,'hub_conf')
    if sync_ol_conf_hub != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_hub_conf_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync hub job.ini from online to local
    sync_ol_conf_hub = sync_ol_data_to_local(ol_info_hub,'hub_info')
    if sync_ol_conf_hub != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_hub_job.ini_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync server data from online to local
    sync_ol_data_server = sync_ol_data_to_local(ol_data_server,'server_data')
    if sync_ol_data_server != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_server_data_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync server data from online to local
    sync_ol_conf_server = sync_ol_data_to_local(ol_conf_server,'server_conf')
    if sync_ol_conf_server != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_server_conf_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync hub job.ini from online to local
    sync_ol_conf_hub = sync_ol_data_to_local(ol_info_server,'server_info')
    if sync_ol_conf_hub != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_server_job.ini_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync hub agent data from online to local
    sync_data_agent_hub = sync_ol_data_to_local(hub_data_agent,'hub_agent')
    if sync_data_agent_hub != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_hub_agent_to_local has some error, pls check"))
        set_status(3)
        return -1

    # rsync server agent data from online to local
    sync_data_agent_server = sync_ol_data_to_local(hub_data_agent,'server_agent')
    if sync_data_agent_hub != 0:
        update_errorlog("[%s] %s\n" % (get_now_time(), "sync_online_server_agent_to_local has some error, pls check"))
        set_status(3)
        return -1

    #testsvn=""
    #basesvn=""


##### config test hub
    if hubsvn.strip() !="":        
        update_errorlog("[%s] %s\n" % (get_now_time(), "try start new hub"))
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build new hub enviroment"))

#        ### check code
#        try:
#            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try check code"))
#            ret = checkcode_env(test_hub, hubsvn)
#        except Exception as e:
#            update_errorlog("[%s] %s\n" % (get_now_time(), e))
#            set_status(3)
#            return -1
#
#        if (ret != 0):
#            set_status(3)
#            return 4
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test check code ok"))
#                
#        ### make
#        try:
#            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try make"))
#            ret = make_env(test_hub)
#        except Exception as e:
#            update_errorlog("[%s] %s\n" % (get_now_time(), e))
#            set_status(3)
#            return -1
#
#        if (ret != 0):
#            set_status(3)
#            return 4
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test make ok"))
        
        
        ### scp new data to test env or cp online to test env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try to configure hub data"))
            if(os.path.exists(test_hub+'/server_frame/data')):
                    loginfo.log_info('testhub_data_dir is exist and del it')
                    os.popen('rm -rf %s' % (test_hub+'/server_frame/data'))
            if hubdatapath == '':
                os.symlink(ol_data_hub,test_hub+'/server_frame/data')
            elif hubcfgip!='' and hubcfguser!='' and hubcfgpassw!='' and hubdatapath!='':
                os.popen('mkdir -p  %s' % (test_hub+'/server_frame/data'))
                scpres = scp_new_file(test_hub+'/server_frame/data',hubcfgip,hubcfguser,hubcfgpassw,hubdatapath,'hub_data')
            else:
                update_errorlog("[%s] %s\n" % (get_now_time(), "test new data configure is wrong"))
                set_status(3)
                return -1
        except Exception as e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1
        update_errorlog("[%s] %s\n" % (get_now_time(), "test hub data ok"))



        ### scp new conf to test env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start to ctrl cfg "))
            if hubcfgpath == '': 
                loginfo.log_info('use cfg online')
                #ret = cp_new_conf(ol_conf_path,test_path)
                cp_cfg(ol_conf_hub,test_hub+'/server_frame/conf')
            elif hubcfgip!='' and hubcfguser!='' and hubcfgpassw!='' and hubcfgpath!='':
                loginfo.log_info('use rd cfg')
                ret = scp_new_file(test_hub+'/server_frame/conf',hubcfgip,hubcfguser,hubcfgpassw,hubcfgpath,'hub_conf')
                
            else:
                update_errorlog("[%s] %s\n" % (get_now_time(), "test new conf configure is wrong"))
                set_status(3)
                return -1
            ret = modify_hub_cfg(test_hub+'/server_frame/conf','12001','18003','18004')
            if ret != 0:
                set_status(3)
                return -1
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1
        update_errorlog("[%s] %s\n" % (get_now_time(), "test conf file ok"))
        

###### just run base
    if sersvn.strip() !="":

#        update_errorlog("[%s] %s\n" % (get_now_time(), "try start to config test server "))
#        update_errorlog("[%s] %s\n" % (get_now_time(), "start try build test server"))
#        ### check code
#        try:
#            update_errorlog("[%s] %s\n" % (get_now_time(), "server01 start try check code"))
#            ret = checkcode_env(test_server+'/server01', sersvn)
#        except Exception as e:
#            update_errorlog("[%s] %s\n" % (get_now_time(), e))
#            set_status(3)
#            return -1
#
#        if (ret != 0):
#            set_status(3)
#            return 4
#        update_errorlog("[%s] %s\n" % (get_now_time(), "server01 check code ok"))
#        
#        ### make
#        try:
#            update_errorlog("[%s] %s\n" % (get_now_time(), "base start try make"))
#            ret = make_env(test_server+'/server01')
#        except Exception as e:
#            update_errorlog("[%s] %s\n" % (get_now_time(), e))
#            set_status(3)
#            return -1
#
#        if (ret != 0):
#            set_status(3)
#            return 4
#        update_errorlog("[%s] %s\n" % (get_now_time(), "base make ok"))
        
#        ### scp new data to test env or cp online to test env
#        try:
#            update_errorlog("[%s] %s\n" % (get_now_time(), "test start try to configure test server01 data"))
#            if(os.path.exists(test_server+'/server01/server_frame/translate_server/data')):
#                    loginfo.log_info('test server01_data_dir is exist and del it')
#                    os.popen('rm -rf %s' % (test_server+'/server01/server_frame/translate_server/data'))
#            if serdatapath == '':
#                os.symlink(ol_data_server,test_server+'/server01/server_frame/translate_server/data')
#            elif sercfgip!='' and sercfguser!='' and sercfgpassw !='' and serdatapath!='':
#                os.popen('mkdir -p  %s' % (test_server+'/server01/server_frame/translate_server/data'))
#                scpres = scp_new_file(test_server+'/server01/server_frame/translate_server/data',sercfgip,sercfguser,sercfgpassw,serdatapath,'server_data')
#            else:
#                update_errorlog("[%s] %s\n" % (get_now_time(), "test server new data configure is wrong"))
#                set_status(3)
#                return -1
#        except Exception as e:
#            update_errorlog("[%s] %s\n" % (get_now_time(), e))
#            set_status(3)
#            return -1
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test server01 data ok"))


	### scp new conf to test env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "test start to deploy server01 cfg "))
            if sercfgpath == '':
                loginfo.log_info('use cfg online')
                #ret = cp_new_conf(ol_conf_path,test_path)
                cp_cfg(ol_conf_server,test_server+'/server01/server_frame/translate_server/conf')
            elif sercfgip!='' and sercfguser!='' and sercfgpassw !='' and serdatapath!='':
                loginfo.log_info('use rd cfg')
                ret = scp_new_file(test_server+'/server01/server_frame/translate_server/conf',sercfgip,sercfguser,sercfgpassw,sercfgpath,'server_data')

            else:
                update_errorlog("[%s] %s\n" % (get_now_time(), "test server new conf configure is wrong"))
                set_status(3)
                return -1
            os.popen("sed -i -e 's/listen_port:.*/listen_port:%s/' %s" %('18003',test_server+'/server01/server_frame/translate_server/conf/eng_trans_server1.cfg'))
            os.popen("sed -i -e '/gpus_to_use:.*[01]/d' %s" %(test_server+'/server01/server_frame/translate_server/conf/eng_trans_server1.cfg'))
            os.popen("sed -i -e '/gpus_to_use:.*3/d' %s" %(test_server+'/server01/server_frame/translate_server/conf/eng_trans_server1.cfg'))
            
            if ret != 0:
                set_status(3)
                return -1
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1
        update_errorlog("[%s] %s\n" % (get_now_time(), "test server01 conf deploy ok"))


        ### cp start.sh to env
        try:
            update_errorlog("[%s] %s\n" % (get_now_time(), "start to cp start_test_server.sh to test server01 env"))
            ret = cp_start_sc(test_server+'/server01/server_frame/translate_server')
        except Exception, e:
            update_errorlog("[%s] %s\n" % (get_now_time(), e))
            set_status(3)
            return -1

        if (ret != 0):
            set_status(3)
            return 4
        update_errorlog("[%s] %s\n" % (get_now_time(), "cp start.sh to base env ok")) 

#        ### deploy server02 from server01
#        try:
#            update_errorlog("[%s] %s\n" % (get_now_time(), "cp hole server01 to server02 and modify cfg"))
#            if os.path.exists(test_server+'/server02'):
#                update_errorlog("[%s] %s dir exists,del it\n" % (get_now_time(), 'server02'))
#                os.popen("rm -rf " + test_server+'/server02')
#            os.popen("cp -r %s  %s/" % (test_server+'/server01', test_server+'/server02'))
#            os.popen("sed -i -e 's/listen_port:.*/listen_port:%s/' %s" %('18004',test_server+'/server02/server_frame/translate_server/conf/eng_trans_server1.cfg'))
#            os.popen("sed -i -e 's/gpus_to_use:.*2/gpus_to_use:3/' %s" %(test_server+'/server02/server_frame/translate_server/conf/eng_trans_server1.cfg'))
#        except Exception, e:
#            update_errorlog("[%s] %s\n" % (get_now_time(), e))
#            set_status(3)
#            return -1
#        update_errorlog("[%s] %s\n" % (get_now_time(), "cp hole server01 to server02 success"))

    #deploy base env
    #hub
    try:
        update_errorlog("[%s] %s\n" % (get_now_time(), "get base hub svn info from job.ini"))
        svninfo_from_job(ol_info_hub,'hub_job_svn')
        print hub_svn_base 
    except Exception as e:
        update_errorlog("[%s] get base hub svn info from job.ini failed\n" % get_now_time(), e)
        set_status(3)
        return -1

    ### check code
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try check base hub code"))
#        ret = checkcode_env(base_hub, hub_svn_base)
#    except Exception as e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    if (ret != 0):
#        set_status(3)
#        return 4
#    update_errorlog("[%s] %s\n" % (get_now_time(), "test check code ok"))
#                
#    ### make
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try make"))
#        ret = make_env(base_hub)
#    except Exception as e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    if (ret != 0):
#        set_status(3)
#        return 4
#    update_errorlog("[%s] %s\n" % (get_now_time(), "test make ok"))
#
#    ### scp new data to test env or cp online to test env
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try to configure base hub data"))
#        if(os.path.exists(base_hub+'/server_frame/data')):
#                loginfo.log_info('base hub_data_dir is exist and del it')
#                os.popen('rm -rf %s' % (test_hub+'/server_frame/data'))
#        os.symlink(ol_data_hub,base_hub+'/server_frame/data')
#    except Exception as e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    update_errorlog("[%s] %s\n" % (get_now_time(), "base hub data ok"))
#
#
#
#    ### scp new conf to test env
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "base hub start to deploy cfg "))
#        loginfo.log_info('use cfg online')
#        #ret = cp_new_conf(ol_conf_path,test_path)
#        cp_cfg(ol_conf_hub,base_hub+'/server_frame/conf')
#        ret = modify_hub_cfg(base_hub+'/server_frame/conf','12000','18001','18002')
#        if ret != 0:
#            set_status(3)
#            return -1
#    except Exception, e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    update_errorlog("[%s] %s\n" % (get_now_time(), "test conf file ok"))
    

    #server
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "get base server01 svn info from job.ini"))
#        svninfo_from_job(ol_info_server,'server_job_svn')
#        print server_svn_base
#    except Exception as e:
#        update_errorlog("[%s] get base server svn info from job.ini failed\n" % get_now_time(), e)
#        set_status(3)
#        return -1
#
#    ### check code
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try check base server code"))
#        ret = checkcode_env(base_server+'/server01', server_svn_base)
#    except Exception as e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    if (ret != 0):
#        set_status(3)
#        return 4
#    update_errorlog("[%s] %s\n" % (get_now_time(), "test server01 check code ok"))
#
#    ### make
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try make server01"))
#        ret = make_env(base_server+'/server01')
#    except Exception as e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    if (ret != 0):
#        set_status(3)
#        return 4
#    update_errorlog("[%s] %s\n" % (get_now_time(), "test server01 make ok"))
#
#    ### scp new data to test env or cp online to test env
#    try:
#        update_errorlog("[%s] %s\n" % (get_now_time(), "test start try to configure base server01 data"))
#        if(os.path.exists(base_server+'/server01/server_frame/translate_server/data')):
#                loginfo.log_info('base server01_data_dir is exist and del it')
#                os.popen('rm -rf %s' % (test_server+'/server01/server_frame/translate_server/data'))
#        os.symlink(ol_data_server,base_server+'/server01/server_frame/translate_server/data')
#    except Exception as e:
#        update_errorlog("[%s] %s\n" % (get_now_time(), e))
#        set_status(3)
#        return -1
#    update_errorlog("[%s] %s\n" % (get_now_time(), "base server01 data ok"))



    ### scp new conf to test env
    try:
        update_errorlog("[%s] %s\n" % (get_now_time(), "base server01 start to deploy cfg "))
        loginfo.log_info('use cfg online')
        #ret = cp_new_conf(ol_conf_path,test_path)
        cp_cfg(ol_conf_server,base_server+'/server01/server_frame/translate_server/conf')
#        ret = modify_hub_cfg(base_hub+'/server_frame/conf','12000','18001','18002')
        if ret != 0:
            set_status(3)
            return -1
    except Exception, e:
        update_errorlog("[%s] %s\n" % (get_now_time(), e))
        set_status(3)
        return -1
    update_errorlog("[%s] %s\n" % (get_now_time(), "test conf file ok"))



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
