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


def update_diffResult(data_content, diff_fk_id):
    db = pymysql.connect('10.134.110.163', 'root', 'Zhangjj@sogou123', 'sogotest')
    cursor = db.cursor()
    sql = "INSERT INTO %s(create_time,user,diff_content,diff_fk_id) VALUES ('%s','%s','%s',%d)" % (
        'webqw_webqwdiffcontent', 'gongyanli', get_now_time(), data_content, diff_fk_id)

    try:
        cursor.execute(sql)
        db.commit()
        print("success")
    except Exception as e:
        print e
        db.rollback()
        pass
    db.close()


def diff_query():
    base = "http://webqw01.web.djt.ted:8019/request"
    test = "http://10.134.100.44:8019/request"

    base_result = ''
    test_result = ''

    data_base_str = ''
    data_test_str = ''

    temp = 0

    with open("query", 'r+') as file:
        for line in file.readlines():
            line = line.replace("\r\n", "")
            headers = {"Content-type": "application/x-www-form-urlencoded;charset=UTF-16LE"}
            base_resp = requests.post(base, data=line, headers=headers)
            test_resp = requests.post(base, data=line, headers=headers)

            data_base = BeautifulSoup(base_resp.text, "html.parser")
            data_test = BeautifulSoup(test_resp.text, "html.parser")

            if data_base.find('srcs_str') != None or data_base.find('dests_str') != None or data_base.find(
                    'level') != None or data_base.find('src_query') != None or data_base.find(
                'clk_qr_dest_node') != None:
                base_result += str(re.findall(r'<(.*?)<config', str(data_base)))
                base_result += str(
                    data_base.find_all(["srcs_str", "dests_str", "level", "src_query", "clk_qr_dest_node", ]))

            if data_base.find('srcs_str') != None or data_base.find('dests_str') != None or data_base.find(
                    'level') != None or data_base.find('src_query') != None or data_base.find(
                'clk_qr_dest_node') != None:
                test_result += str(re.findall("(.*?)<config", str(data_test)))
                test_result += str(
                    data_test.find_all(["srcs_str", "dests_str", "level", "src_query", "clk_qr_dest_node", ]))

            temp += 1

            if temp == 3:
                base_result = base_result.replace("'", '').replace('[', '').replace(']', '').replace(',', '')
                test_result = base_result.replace("'", '').replace('[', '').replace(']', '').replace(',', '')

                base_result = BeautifulSoup(str(base_result), "html.parser")
                test_result = BeautifulSoup(str(test_result), "html.parser")

                diff = difflib.HtmlDiff()
                # data = diff.make_table(str(base_result).splitlines(), str(test_result).splitlines())
                data = diff.make_table(base_result.prettify().splitlines(), test_result.prettify().splitlines())
                data = cgi.escape(data.replace("'", "&#39;"), quote=True)
                update_diffResult(data, 68)
                base_result = ''
                test_result = ''

                temp = 0

        base_result = BeautifulSoup(str(base_result), "html.parser")
        test_result = BeautifulSoup(str(test_result), "html.parser")
        diff = difflib.HtmlDiff()
        # data = diff.make_table(str(base_result).splitlines(), str(test_result).splitlines())
        # data = diff.make_table(data_base_str.prettify().splitlines(), data_test_str.prettify().splitlines())
        data = diff.make_table(base_result.prettify().splitlines(), test_result.prettify().splitlines())

        data = cgi.escape(data.replace("'", "&#39;"), quote=True)

        update_diffResult(data, 68)

        file.close()

    # data = diff.make_file(data_base_str.prettify().splitlines(), data_test_str.prettify().splitlines()).replace('nowrap="nowrap"', '')

    return 0


if __name__ == '__main__':
    diff_query()
# update_diffResult("data",68)
