#! /usr/bin/env python
#coding=utf-8
#status：任务的状态（0:未开始；1:已分配；2正在运行；3:出错停止；4:已完成；5:任务取消；6:准备取消）
import os

autoqps_path = "/search/odin/daemon/automission/webqo"

online_host = "rsync.webqo01.web.1.djt.ted"
online_path = "/search/odin/daemon/qo"

#offline_host = "rsync.datatest01.web.sjs.ted"
#offline_path = "/search/odin/autotest/query"


#local_tmp_data_path = "/search/data2/tmp_data/"
#test_query_disk_root = "/search/data2/test_query/"
#update_tmp_file = '/tmp/.is_autotest_update'

#output = os.popen("sogou-host -a | head -1")
#local_ip = output.read().replace('\n', '')
local_ip='10.144.82.27'
root_path="/search/odin/daemon/webqo/"

test_path_1="qo_test"
base_path_1="qo_base"

ol_data_path_1="/search/summary_o/webqo"
ol_conf_path_1="tmp_conf"

black_data_path="/search/odin/daemon/black_agent/data"

cost_tool = os.path.join(root_path, "tools/log_analysis.py")
start_sc = os.path.join(root_path, "tools/start.sh")

#press conf
sggp_path = os.path.join(root_path, "tools/sggp")
sggp_conf = os.path.join(root_path, "tools/sggp/web_qo.ini")
sggp_query_path = os.path.join(root_path, "tools/sggp/data/")
runlogbak = os.path.join(root_path, "logbak/")

#database conf
database_host="10.134.110.163"
database_data="sogotest"
database_table="webqo_webqoqps"
database_user="root"
database_pass="Zhangjj@sogou123"



log_file = os.path.join(autoqps_path, "log/autorun.log")
