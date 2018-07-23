#!/usr/bin/python
import sys
import requests
import random
import difflib
import time
import pymysql
import base64
import re
import cgi
import HTMLParser
from xml.etree import ElementTree
from bs4 import BeautifulSoup
reload(sys)
sys.setdefaultencoding('utf-8')


def get_now_time():
    timeArray = time.localtime()
    return  time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

def insert_finished(finished,diff_task_id):
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    up_sql = "UPDATE %s set finished=%d where id=%d" % ('fanyi_fydiff', finished ,diff_task_id)
    try:
        cursor.execute(up_sql)
        db.commit()
    except Exception as e:
        print e
        db.rollback()
        pass
    db.close()

def insert_diff_data(diffcontent,diffnum,diff_task_id):
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    
    update_sql = "UPDATE %s set diffnum=%d where id=%d" % ('fanyi_fydiff',diffnum,diff_task_id)
    try:
        cursor.execute(update_sql)
        db.commit()
    except Exception as e:
        print e
        db.rollback()
        pass

    sql = "INSERT INTO %s(create_time,user,diff_content,diff_task_id) VALUES ('%s','%s','%s',%d)" % ('fanyi_diffcontent', 'zhangjingjun',get_now_time() ,diffcontent,diff_task_id)
   
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        print e
        db.rollback()
        pass
    db.close()

def parseXmlRes(xml_str):
    result_dic=dict()
    ns={'parent':'http://schemas.xmlsoap.org/soap/envelope/','child':'http://fanyi.sogou.com/'}
    try:
        root=ElementTree.fromstring(xml_str)
    except Exception,e:
        result_dic['wrongres']='wrongres:'+str(e)
        result_dic['transRes']='Error request'
        return result_dic
    try:
        tempNum = random.randint(1,3)
        for node in root.findall('parent:Body',ns):
            for body in node.findall('child:TranslateResponse',ns):
                if body.find('child:TranslateResult',ns) is not None:
                    if body.find('child:TranslateResult',ns).text is not None:
                        result_dic['transRes']=body.find('child:TranslateResult',ns).text + str(tempNum)
                    else:
                        result_dic['transRes']='Error request'
                else:
                    result_dic['transRes']='Error request'
    except Exception,e:
        result_dic['wrongres']='wrongres:'+str(e)
        result_dic['transRes']='Error request'
    if 'transRes' not in result_dic:
        result_dic['transRes']='Error request'
    return result_dic

def getUniNum(string):
    try:
        string=string.strip()
        query=""
        for uchar in string:
            query+="&#"+str(ord(uchar))+";"
        return query
    except Exception as e:
            print e

def decodeHtml(input_str):
    h = HTMLParser.HTMLParser()
    s = h.unescape(input_str)
    return s


def getDiff(query_tools_path,filename,fromlang,tolang,mission_id):
    base_diff_content = ''
    test_diff_content = ''
    tmp = 0
    finished = 0
    diffnum = 0
    with open(query_tools_path+'query/'+filename,'r') as fin,open(query_tools_path+'result_log/'+'base_res_'+str(mission_id),'w') as fw_base,open(query_tools_path+'result_log/'+'test_res_'+str(mission_id),'w') as fw_test,open(query_tools_path+'result_log/'+'all_req_'+str(mission_id),'w') as allo:
        for item in fin.readlines():
            finished +=1
            item = item.strip()
            #query = getUniNum(item)
            xmldata = '''<?xml version="1.0" encoding="UTF-8"?><soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:v2="http://api.microsofttranslator.com/V2"><soapenv:Header/><soapenv:Body><v2:Translate><v2:appId></v2:appId><v2:text>{_reqtext}</v2:text><v2:from>{_fromlan}</v2:from><v2:to>{_tolan}</v2:to><v2:needQc>0</v2:needQc><v2:contentType>text/plain</v2:contentType><v2:category>general</v2:category></v2:Translate></soapenv:Body></soapenv:Envelope>'''.format(_reqtext=item, _fromlan=fromlang, _tolan=tolang)
            result_base=dict()
            result_test=dict()
            try:
                resp_base = requests.post('http://10.153.51.60:12000/xml', data=xmldata)
                result_base = parseXmlRes(resp_base.text)
            except Exception as e :
                result_base['transRes']='base request http error'
                pass
            try:
                resp_test = requests.post('http://10.153.51.60:12001/xml', data=xmldata)
                result_test = parseXmlRes(resp_test.text)
            except Exception as e :
                result_test['transRes']='test request http error'
                pass
          
            allo.write('Query:'+item.decode('utf-8')+'\n')
            allo.write('base:'+resp_base.text+'result:'+result_base['transRes']+'\n')
            allo.write('base:'+resp_test.text+'result:'+result_test['transRes']+'\n')
            if (result_base['transRes'] != result_test['transRes']):
                base_diff_content += ('Query:'+item.decode('utf-8')+'\n'+result_base['transRes']+'\n')
                test_diff_content += ('Query:'+item.decode('utf-8')+'\n'+result_test['transRes']+'\n')
                fw_base.write('Query:'+item.decode('utf-8')+'\n'+result_base['transRes']+'\n')
                fw_test.write('Query:'+item.decode('utf-8')+'\n'+result_test['transRes']+'\n')
                tmp+=1
                diffnum+=1
            if tmp == 50:
                d = difflib.HtmlDiff()
                diff_html = d.make_file(base_diff_content.splitlines(),test_diff_content.splitlines())
                parse_html = BeautifulSoup(diff_html,"html.parser")                
                escape_str = cgi.escape(str(parse_html.table),quote=True)
                #b = decodeHtml(a)
                #print 'bbbbb'+b.encode('utf-8')
                insert_diff_data(escape_str.replace("'","&#39;"),diffnum,mission_id)
                base_diff_content=''
                test_diff_content=''
                tmp=0
            if (finished%1000)==0:
                insert_finished(finished,mission_id)
        d = difflib.HtmlDiff()
        diff_html = d.make_file(base_diff_content.splitlines(),test_diff_content.splitlines())
        parse_html = BeautifulSoup(diff_html,"html.parser")
        escape_str = cgi.escape(str(parse_html.table),quote=True)
        #b = decodeHtml(a)
        #print 'bbbbb'+b.encode('utf-8')
        try:
            insert_diff_data(escape_str.replace("'","&#39;"),diffnum,mission_id)
        except Exception as e:
            print e
        insert_finished(finished,mission_id)


if __name__ == '__main__':
    queryFile = sys.argv[1]
    from_lang = 'ja'
    to_lang = 'zh-CHS'
    getDiff('/search/odin/daemon/fanyi/tools/',queryFile,from_lang,to_lang,32)
