#! /usr/bin/env python
#coding=utf-8
#status：任务的状态（0:未开始；1:已分配；2正在运行；3:出错停止；4:已完成；5:任务取消；6:准备取消）
import os

autoqps_path = "/search/odin/daemon/zhangjj/automission/sg_auto_server"

online_host_hub = "rsync.ywhub01.fy.sjs.ted"
online_path_hub = "/search/odin/daemon/uniq_trans_hub1"

online_host_server = "rsync.ywserver01.fy.sjs.ted"
online_path_server = "odin/search/odin/daemon/eng_trans_server1"

hub_data_agent = "/search/odin/daemon/data_agent/data/base"
server_data_agent = "odin/search/odin/daemon/data_agent/data/base"

local_ip='10.153.51.61'

root_path="/search/odin/daemon/translate/"

test_hub_path = "hub/hub_test"
test_server_path = "server/server_test"

base_hub_path = "hub/hub_base"
base_server_path = "server/server_base"

online_data_hub="tmp_data/hub"
online_data_server="tmp_data/server"

online_conf_hub="tmp_conf/hub"
online_conf_server="tmp_conf/server"

online_job_hub="tmp_info/hub"
online_job_server="tmp_info/server"


start_sc_test = os.path.join(root_path, "tools/start_test_server.sh")
start_sc_base = os.path.join(root_path, "tools/start_base_server.sh")
start_sc_hub = os.path.join(root_path, "tools/start_hub.sh")

#press conf
sggp_path = os.path.join(root_path, "tools/sggp")
sggp_conf = os.path.join(root_path, "tools/sggp/web_qo.ini")
sggp_query_path = os.path.join(root_path, "tools/sggp/data/")

runlogbak = os.path.join(root_path, "logbak/")

#database conf
database_host="10.134.110.163"
database_data="sogotest"
database_table="fanyi_fydiff"
database_user="root"
database_pass="Zhangjj@sogou123"



