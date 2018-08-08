#! /usr/bin/env python
# coding=utf-8

import requests
import difflib
from bs4 import BeautifulSoup


def diff_query():
    base = "http://webqw01.web.djt.ted:8019/request"
    test = "http://10.134.100.44:8019/request"

    data_base = []
    data_test = []

    with open("/search/odin/daemon/longdiff/longdiff_query", 'r+') as file:
        for line in file.readlines():
            line = line.replace("\r\n", "")
            headers = {"Content-type": "application/x-www-form-urlencoded;charset=UTF-16LE"}
            base_resp = requests.post(base, data=line, headers=headers)
            test_resp = requests.post(test, data=line, headers=headers)

            data_base.append(base_resp.text.encode("GBK"))
            data_test.append(test_resp.text.encode("GBK"))

        file.close()

    data_base_str = BeautifulSoup(''.join(data_base), "html.parser")
    data_test_str = BeautifulSoup(''.join(data_test), "html.parser")

    diff = difflib.HtmlDiff()

    data = diff.make_table(data_base_str.prettify().splitlines(), data_test_str.prettify().splitlines()).replace(
        'nowrap="nowrap"', '')

    return data
