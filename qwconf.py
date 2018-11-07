#! /usr/bin/env python
#coding=utf-8
#status：任务的状态（0:未开始；1:已分配；2正在运行；3:出错停止；4:已完成；5:任务取消；6:准备取消）
import os

autoqps_path = "/search/odin/daemon/automission/webqw"  # 工具路径地址

online_host = "rsync.webqw01.web.djt.ted"  # 线上host
online_path = "/search/odin/daemon/qw"      # 线上路径

#offline_host = "rsync.datatest01.web.sjs.ted"
#offline_path = "/search/odin/autotest/query"


#local_tmp_data_path = "/search/data2/tmp_data/"
#test_query_disk_root = "/search/data2/test_query/"
#update_tmp_file = '/tmp/.is_autotest_update'

#output = os.popen("sogou-host -a | head -1")
#local_ip = output.read().replace('\n', '')
local_ip='10.134.100.44'                        # 本地ip
root_path="/search/odin/daemon/webqw/"          # 本地地址

test_path_1="qw_test"                           # 本地测试路径
base_path_1="qw_base"                           # 线上测试路径

ol_data_path_1="/search/summary_o/webqw"        # 线上数据文件
ol_conf_path_1="tmp_conf"                       # 线上配置文件

black_data_path="/search/odin/daemon/black_agent/data"          # 黑名单数据存放位置

cost_tool = os.path.join(root_path, "tools/log_analysis.py")    # cost分析工具存放位置
start_sc = os.path.join(root_path, "tools/start.sh")            # sggp压力工具启动文件

# diff配置文件
diff_path="/search/odin/daemon/longdiff"

#press conf
sggp_path = os.path.join(root_path, "tools/sggp")
sggp_query_path = os.path.join(root_path, "tools/sggp/data/")
# runlogbak = os.path.join(root_path, "logbak/")
runlogbak="/search/summary_o/webqw/logbak/"

#database conf
database_host="10.144.120.30"
database_data="sogowebqa"
database_table="webqw_qps"
database_user="root"
database_pass="Websearch@qa66"



log_file = os.path.join(autoqps_path, "log/autorun.log")
