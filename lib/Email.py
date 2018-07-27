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
        'body': body.encode('GBk'),
        'mode': 'html',
        'maillist': maillist,
        'attname': attname,
        'attbody': attbody,
    }
    try:
        resp = requests.post(url, data=params)
        print('successfully')
    except Exception as e:
        print('error',e)


#sendEmail("test", 'testtest', 'gongyanli@sogou-inc.com;zhangjingjun@sogou-inc.com')

