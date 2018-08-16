#! /usr/bin/env python
# coding=utf-8

import requests
import difflib
from bs4 import BeautifulSoup
import re
import pymysql
import cgi
import time


def get_now_time():
    timeArray = time.localtime()
    return time.strftime("%Y-%m-%d %H:%M:%S", timeArray)


def update_qw_diffResult(data_content, diff_fk_id):
    db = pymysql.connect('10.134.110.163', 'root', 'Websearch@qa66', 'sogotest',use_unicode=True, charset='utf8')
    cursor = db.cursor()
    sql = "INSERT INTO %s(create_time,user,diff_content,diff_fk_id) VALUES ('%s','%s','%s',%d)" % (
        'webqw_webqwdiffcontent', 'gongyanli', get_now_time(), data_content, diff_fk_id)

    try:
        cursor.execute(sql)
        db.commit()
        # print("success webqw")
    except Exception as e:
        print e
        db.rollback()
        pass
    db.close()


def update_qo_diffResult(data_content, diff_fk_id):
    db = pymysql.connect('10.134.110.163', 'root', 'Websearch@qa66', 'sogotest',use_unicode=True, charset='utf8')
    cursor = db.cursor()
    sql = "INSERT INTO %s(create_time,user,diff_content,diff_fk_id) VALUES ('%s','%s','%s',%d)" % (
        'webqo_webqodiffcontent', 'gongyanli', get_now_time(), data_content, diff_fk_id)

    try:
        cursor.execute(sql)
        db.commit()
        # print("success webqo ")
    except Exception as e:
        print e
        db.rollback()
        pass
    db.close()


def diff_query(base, test, mission_id):
    # base = "http://webqw01.web.djt.ted:8019/request"
    # test = "http://10.134.100.44:8019/request"

    base_result_qw = ''
    test_result_qw = ''

    base_result_qo = ''
    test_result_qo = ''

    temp_qw = 0
    temp_qo = 0

    if base == "http://webqw01.web.djt.ted:8019/request":

        with open("/search/odin/daemon/qw_diff/longdiff/longdiff_query", 'r+') as file:
            for line in file.readlines():
                line = line.replace("\r\n", "")
                headers = {"Content-type": "application/x-www-form-urlencoded;charset=UTF-16LE"}
                base_resp = requests.post(base, data=line, headers=headers)
                test_resp = requests.post(test, data=line, headers=headers)

                if base_resp.text!=test_resp.text:

                    data_base = BeautifulSoup(base_resp.text.encode('utf-8'), "html.parser")
                    data_test = BeautifulSoup(test_resp.text.encode('utf-8'), "html.parser")

                    if data_base.find('srcs_str') != None or data_base.find('dests_str') != None or data_base.find(
                            'level') != None or data_base.find('src_query') != None or data_base.find(
                        'clk_qr_dest_node') != None:
                        base_result_qw += str(re.findall(r'<(.*?)<config', str(data_base)))
                        base_result_qw += str(
                            data_base.find_all(["srcs_str", "dests_str", "level", "src_query", "clk_qr_dest_node", ]))

                    if data_test.find('srcs_str') != None or data_test.find('dests_str') != None or data_test.find(
                            'level') != None or data_test.find('src_query') != None or data_test.find(
                        'clk_qr_dest_node') != None:
                        test_result_qw += str(re.findall("<(.*?)<config", str(data_test)))
                        test_result_qw += str(
                            data_test.find_all(["srcs_str", "dests_str", "level", "src_query", "clk_qr_dest_node", ]))

                    temp_qw += 1

                if temp_qw == 3:
                    base_result_qw = base_result_qw.replace("'", '').replace('[', '').replace(']', '').replace(',', '')
                    test_result_qw = test_result_qw.replace("'", '').replace('[', '').replace(']', '').replace(',', '')

                    base_result_qw = BeautifulSoup(str(base_result_qw), "html.parser")
                    test_result_qw = BeautifulSoup(str(test_result_qw), "html.parser")

                    diff = difflib.HtmlDiff()
                    # data = diff.make_table(str(base_result).splitlines(), str(test_result).splitlines())
                    data_qw = diff.make_table(base_result_qw.prettify().splitlines(),
                                              test_result_qw.prettify().splitlines())
                    data_qw = cgi.escape(data_qw.replace("'", "&#39;"), quote=True)
                    update_qw_diffResult(data_qw, mission_id)
                    base_result_qw = ''
                    test_result_qw = ''

                    temp_qw = 0


            base_result_qw = BeautifulSoup(str(base_result_qw), "html.parser")
            test_result_qw = BeautifulSoup(str(test_result_qw), "html.parser")
            diff_qw = difflib.HtmlDiff()
            # data = diff.make_table(str(base_result).splitlines(), str(test_result).splitlines())
            # data = diff.make_table(data_base_str.prettify().splitlines(), data_test_str.prettify().splitlines())
            data_qw = diff_qw.make_table(base_result_qw.prettify().splitlines(), test_result_qw.prettify().splitlines())

            data_qw = cgi.escape(data_qw.replace("'", "&#39;"), quote=True)

            update_qw_diffResult(data_qw, mission_id)

        file.close()

        return 0

    elif base == "http://webqo01.web.djt.ted:8012/request":
        with open("/search/odin/daemon/qo_diff/longdiff/longdiff_query", 'r+') as file:
            for line in file.readlines():
                line = line.replace("\r\n", "")
                headers = {"Content-type": "application/x-www-form-urlencoded;charset=UTF-16LE"}
                base_resp = requests.post(base, data=line, headers=headers)
                test_resp = requests.post(test, data=line, headers=headers)

                if base_resp.text!=test_resp.text:
                    base_result_qo += base_resp.text.encode('utf-8')
                    test_result_qo += test_resp.text.encode('utf-8')
                    temp_qo += 1

                if temp_qo == 3:
                    # base_result = base_resp.text.replace("'", '').replace('[', '').replace(']', '').replace(',', '')
                    # test_result = test_resp.text.replace("'", '').replace('[', '').replace(']', '').replace(',', '')

                    base_result_qo = BeautifulSoup(str(base_result_qo), "html.parser")
                    test_result_qo = BeautifulSoup(str(test_result_qo), "html.parser")

                    diff = difflib.HtmlDiff()
                    # data = diff.make_table(str(base_result).splitlines(), str(test_result).splitlines())
                    data_qo = diff.make_table(base_result_qo.prettify().splitlines(),
                                              test_result_qo.prettify().splitlines())
                    data_qo = cgi.escape(data_qo.replace("'", "&#39;"), quote=True)
                    update_qo_diffResult(data_qo, mission_id)
                    base_result_qo = ''
                    test_result_qo = ''

                    temp_qo = 0

            base_result = BeautifulSoup(str(base_result_qo), "html.parser")
            test_result = BeautifulSoup(str(test_result_qo), "html.parser")
            diff_qo = difflib.HtmlDiff()
            # data = diff.make_table(str(base_result).splitlines(), str(test_result).splitlines())
            data_qo = diff_qo.make_table(base_result.prettify().splitlines(), test_result.prettify().splitlines())

            data_qo = cgi.escape(data_qo.replace("'", "&#39;"), quote=True)

            update_qo_diffResult(data_qo, mission_id)

        file.close()

        return 0


if __name__ == '__main__':
    # diff_query("http://webqw01.web.djt.ted:8019/request", "http://webqw01.web.djt.ted:8019/request",68)
    diff_query("http://webqo01.web.djt.ted:8012/request", "http://webqo01.web.djt.ted:8012/request",188)
# update_diffResult("data",68)
