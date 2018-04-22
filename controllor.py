#! /usr/bin/env python
#coding=utf-8
import subprocess
import pymysql
import time
from conf import *


db = pymysql.connect(database_host,database_user,database_pass,database_data)
cursor = db.cursor()

log_fd = open(log_file, 'w')

def get_running_id():
    sql = "SELECT id FROM {_table} where status=2 and runningIP='{_ip}' limit 1".format(_table=data_table,_ip=local_ip)
    cursor.execute(sql)
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    return -1
def get_my_id():
    sql = "SELECT id FROM {_table} where status=1 and runningIP='{_ip}' limit 1".format(_table=data_table,_ip=local_ip)
    cursor.execute(sql)
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    return -1
def get_cancel_id():
    sql = "SELECT id FROM {_table} where status=6 and runningIP='{_ip}' limit 1".format(_table=data_table,_ip=local_ip)
    cursor.execute(sql)
    data = cursor.fetchone()
    if data is not None:
        return data[0]
    return -1

def main():
    task_list = {}
    while True:
        time.sleep(2)
        running_id = get_running_id();
        if (running_id != -1):
            continue
        for (k, v) in task_list.items():
            if (v.poll() != None):
                del task_list[k]
        mission_id = get_my_id()
        print mission_id
        if mission_id is -1:
            print "no mission"
        else:
            child = subprocess.Popen(['/bin/python3', 'qoqps_runner.py','%d' % mission_id], shell = False, stdout = log_fd, stderr = log_fd, cwd=autoqps_path)
            task_list[mission_id] = child
        cancel_id = get_cancel_id()
        if cancel_id is -1:
            continue
        if cancel_id in task_list:
            task_list[cancel_id].send_signal(10)
        else:
            sql = "UPDATE {_table} set status = 5 WHERE id = {_cancel_id}".format(_table=data_table,_cancel_id=cancel_id)
            cursor.execute(sql)
            try:
                db.commit()
            except:
                db.rollback()

if __name__ == '__main__':
    main()
