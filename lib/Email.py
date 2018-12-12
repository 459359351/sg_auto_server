#! /usr/bin/env python
# coding=utf-8

import requests

# email:getÇÇ
# r = requests.get(
#     "http://mail.portal.sogou/portal/tools/send_mail.php?uid=gongyanli@sogou-inc.com&fr_name=¹¨ÑÀ&fr_addr=gongyanli@sogou-inc.com&title=test&body=test&mode=html&maillist=gongyanli@sogou-inc.com&attname=test.txt&attbody=²â¸½¼þÎ±¾")


# email:postÇÇ
def sendEmail(fr_name, title, body, maillist, attname=None, attbody=None):
    url = "http://mail.portal.sogou/portal/tools/send_mail.php"
    params = {
        'uid': 'gongyanli@sogou-inc.com',
        'fr_name': fr_name,
        'fr_addr': 'gongyanli@sogou-inc.com',
        'title': title,
        'body': body.decode('utf-8'),
        'mode': 'html',
        'maillist': maillist,
        'attname': attname,
        'attbody': attbody,
    }
    try:
        resp = requests.post(url, data=params)
        print(resp.status_code)
        print('successfully')
    except Exception as e:
        print('error',e)


if __name__=='__main__':
    data='nihao'
    body_head = """<html><head><style type="text/css">table{border-collapse:collapse;margin:0 auto;text-align:left;}table td,table th{border:1px solid #cad9ea;color:#666;height:30px;}table thead th{background-color:#CCE8EB;width:100px;}table tr:nth-child(odd){background:#fff;}table tr:nth-child(even){background:#F5FAFA;}</style></head><table width='90%' class='table'><thead><tr><th>机器名称</th><th>返回结果</th></tr></thead>"""

    body_content = """<tr><td>%s</td><td>%s</td></tr></table></body></html>"""
    body = body_head + body_content % (data, data)

    sendEmail('机器翻译-线上机器-【Time out or NULL】',"Time out or NULL ", body, 'gongyanli@sogou-inc.com')

