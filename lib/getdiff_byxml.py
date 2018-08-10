#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import requests
import random
import difflib
import time
import pymysql
import logUtils
import base64
import re
import cgi
import HTMLParser
import os
import pexpect
from xml.etree import ElementTree
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding('utf-8')

root_path = '/search/odin/daemon/fanyi/tools/'
database_table = 'fanyi_fyxmldiff'
task_id = int(sys.argv[1])

def get_now_time():
    timeArray = time.localtime()
    return  time.strftime("%Y-%m-%d %H:%M:%S", timeArray)

def insert_finished(finished,diff_task_id):
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    up_sql = "UPDATE %s set finished=%d where id=%d" % ('fanyi_fyxmldiff', finished ,diff_task_id)
    try:
        cursor.execute(up_sql)
        db.commit()
    except Exception as e:
        db.rollback()
        pass
    db.close()

def insert_diff_data(diffcontent,diffnum,diff_task_id):
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest',charset='utf8')
    cursor = db.cursor()
    
    update_sql = "UPDATE %s set diffnum=%d where id=%d" % ('fanyi_fyxmldiff',diffnum,diff_task_id)
    try:
        cursor.execute(update_sql)
        db.commit()
    except Exception as e:
        print e
        db.rollback()
        pass
    sql = "INSERT INTO %s(create_time,user,diff_content,diff_task_id) VALUES ('%s','%s','%s',%d)" % ('fanyi_xmldiffcontent', 'zhangjingjun',get_now_time() ,diffcontent,diff_task_id)
   
    try:
        cursor.execute(sql)
        db.commit()
    except Exception as e:
        db.rollback()
        print e
        pass
    db.close()

def parseXmlReq(xml_str):
    query_lst_info=dict()
    if xml_str=="":
        return query_lst_info
    xmlns={'soapenv':'http://schemas.xmlsoap.org/soap/envelope/',
         'v2':'http://api.microsofttranslator.com/V2'}
    try:
        root=ElementTree.fromstring(xml_str)
    except Exception,e:
        query_lst_info['wrongreq']='wrong request,reson:'+str(e)
        query_lst_info['qtext'] = 'parseWrong'
        return query_lst_info
    try:
        for node in root.findall('soapenv:Body',xmlns):
            for Translate in node.findall('v2:Translate',xmlns):
                if Translate.find('v2:text',xmlns) is not None:
                    query_lst_info['qtext']=Translate.find('v2:text',xmlns).text.encode('utf-8')
                else:
                    query_lst_info['qtext']='parseWrong'
                if Translate.find('v2:from',xmlns) is not None:
                    query_lst_info['qfrom']=Translate.find('v2:from',xmlns).text.encode('utf-8')
                else:
                    query_lst_info['qfrom']=''
                if Translate.find('v2:to',xmlns) is not None:
                    query_lst_info['qto']=Translate.find('v2:to',xmlns).text.encode('utf-8')
                else:
                    query_lst_info['qto']=''
    except Exception,e:
        query_lst_info['wrongreq']='wrong request,reson:'+str(e)
        query_lst_info['qtext'] = 'parseWrong'
    return query_lst_info


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
                        result_dic['transRes']=body.find('child:TranslateResult',ns).text
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
        pass

def decodeHtml(input_str):
    h = HTMLParser.HTMLParser()
    s = h.unescape(input_str)
    return s


def getDiff(query_tools_path,filename,mission_id,base_url,test_url):
    base_diff_content = ''
    test_diff_content = ''
    tmp = 0
    finished = 0
    diffnum = 0
    with open(query_tools_path+'query/'+filename,'r') as fin,open(query_tools_path+'result_log/'+'base_res_'+str(mission_id),'w') as fw_base,open(query_tools_path+'result_log/'+'test_res_'+str(mission_id),'w') as fw_test,open(query_tools_path+'result_log/'+'all_req_'+str(mission_id),'w') as allo:
        set_status(2)
        for item in fin.readlines():
            finished +=1
            item = item.strip()
            reqInfo = parseXmlReq(item)
            if reqInfo['qtext'] == 'parseWrong':
                continue
            xmldata = item
            result_base=dict()
            result_test=dict()
            try:
                resp_base = requests.post('http://'+base_url+'/xml', data=xmldata)
                result_base = parseXmlRes(resp_base.text)
            except Exception as e :
                result_base['transRes']='base request http error'
                pass
            try:
                resp_test = requests.post('http://'+test_url+'/xml', data=xmldata)
                result_test = parseXmlRes(resp_test.text)
            except Exception as e :
                result_test['transRes']='test request http error'
                pass
          
            allo.write('Query:'+item.decode('utf-8')+'\n')
            allo.write('base:'+resp_base.text+'result:'+result_base['transRes']+'\n')
            allo.write('base:'+resp_test.text+'result:'+result_test['transRes']+'\n')
            if (result_base['transRes'] != result_test['transRes']):
                base_diff_content += ('Query:'+reqInfo['qtext']+' from:'+reqInfo['qfrom']+' to:'+reqInfo['qto']+'\n'+result_base['transRes'].decode('utf-8')+'\n')
                test_diff_content += ('Query:'+reqInfo['qtext']+' from:'+reqInfo['qfrom']+' to:'+reqInfo['qto']+'\n'+result_test['transRes'].decode('utf-8')+'\n')
                fw_base.write('Query:'+reqInfo['qtext']+'from:'+reqInfo['qfrom']+'to:'+reqInfo['qto']+'\n'+result_base['transRes']+'\n')
                fw_test.write('Query:'+reqInfo['qtext']+'from:'+reqInfo['qfrom']+'to:'+reqInfo['qto']+'\n'+result_test['transRes']+'\n')
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
        set_status(4)

def getInfoFromDb(task_id):
    update_errorlog("[%s] Get task info from db by id \n" % get_now_time())
    try:
        db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
        cursor = db.cursor()
        sql = "SELECT test_url,base_url,queryip,queryuser,querypassw,querypath FROM %s where id='%d'" % ('fanyi_fyxmldiff',task_id)
        cursor.execute(sql)
        data = cursor.fetchone()
        logstr.log_info("test_url:"+data[0]+'\n'+'base_url:'+data[1]+'\n'+'queryip:'+data[2]+'\n'+'queryuser:'+data[3]+'\n'+'querypassw:'+data[4]+'\n'+'querypath:'+data[5])
    except Exception as e:
        set_status(3)
        update_errorlog("[%s] Get task info error from db by id \n" % get_now_time())
        logstr.log_info("[%s] Get task info error from db by id,error info:%s" % (get_now_time(),str(e)))
        sys.exit()
    update_errorlog("[%s] Get task info from db by id success\n" % get_now_time())
    return data
    
def getQueryFile(root_path):
    # scp query to tools dir
    try:
        update_errorlog("[%s] %s\n" % (get_now_time(), "start try to scp query data"))
        if(os.path.exists(root_path+'query')):
            logstr.log_info('query dir is exist')
            oldfile = os.listdir(root_path+'query')
            timeArray = time.localtime()
            filename = time.strftime("%Y-%m-%d_%H%M%S", timeArray)
            if oldfile:
                for item in oldfile:
                    os.popen('mv %s %s' % (root_path+'query/'+item,root_path+'query_bak/'+filename+'_'+item))
        if queryip!='' and queryuser!='' and querypassw!='' and querypath!='':
            scpres = scp_new_file(root_path+'query',queryip,queryuser,querypassw,querypath,'query_data')
        else:
            update_errorlog("[%s] %s\n" % (get_now_time(), "query data configure is wrong"))
            set_status(3)
            sys.exit()
        filelist = os.listdir(root_path+'query')
    except Exception as e:
        update_errorlog("[%s] Get query file error\n" % get_now_time())
        logstr.log_info("[%s] Get query file error ,error info:%s" % (get_now_time(),str(e)))
        set_status(3)
        sys.exit()
    update_errorlog("[%s] %s\n" % (get_now_time(), "query data scp local success"))
    return filelist[0]

def scp_new_file(file_path,newfileip,newfileuser,newfilepassw,newfilepath,filetype):
    update_errorlog("[%s] try scp rd %s to test enviroment\n" % (get_now_time(),filetype))
    if filetype != 'query_data':
        if os.path.exists(file_path):
            update_errorlog("[%s] %s dir exists,del it\n" % (get_now_time(), filetype))
            os.popen("rm -rf " + file_path)

    passwd_key = '.*assword.*'

    cmdline = 'scp -r %s@%s:%s %s/' %(newfileuser, newfileip, newfilepath, file_path)
    try:
        child=pexpect.spawn(cmdline,maxread=20000,timeout=300)
        os.popen("set timeout -1")
        expect_result = child.expect([r'assword:',r'yes/no', pexpect.EOF, pexpect.TIMEOUT])
        if expect_result == 0:
            child.sendline(newfilepassw)
            os.popen("set timeout -1")
        elif expect_result ==1:
            child.sendline('yes')
            child.expect(passwd_key,timeout=30)
            child.sendline(newfilepassw)
        child.expect(pexpect.EOF)

    except Exception as e:
        update_errorlog("[%s] %s, scp rd %s failed \n" % (get_now_time(), e,filetype))
    update_errorlog("[%s] try scp rd %s to test enviroment success\n" % (get_now_time(),filetype))
    return 0

def update_errorlog(log):
    log = log.replace("'", "\\'")
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    sql = "UPDATE %s set errorlog=CONCAT(errorlog, '%s') where id=%d;" % (database_table, log, task_id)
    cursor.execute(sql)
    data = cursor.fetchone()
    logstr.log_info(str(task_id)+"\t"+log)
    try:
        db.commit()
    except:
        logstr.log_debug("error")

def set_status(stat):
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    sql = "UPDATE %s set status=%d where id=%d" % (database_table, stat, task_id)
    cursor.execute(sql)
    db.commit()

def set_subpid(subpid,status):
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    sql = "UPDATE %s set start_time='%s',runningPID='%s',status=%d where id=%d;" % (database_table, get_now_time(),subpid, status,int(task_id))
    cursor.execute(sql)
    try:
        db.commit()
        logstr.log_info('Update PID task ,sql is '+ sql)
    except Exception as e:
        db.rollback()
        logstr.log_info('Update PID task failed')

def sendMail(title,mail_body,tlist,attname,attbody):
    mail_url = 'http://mail.portal.sogou/portal/tools/send_mail.php'
    mail_Info = {
    'uid' : "zhangjingjun@sogou-inc.com",
    'fr_name' : 'Fyxml Autodiff',
    'fr_addr' : "zhangjingjun@sogou-inc.com",
    'title' : title.encode('GBK'),
    'body' : mail_body.encode('GBK'), #use nl2br to adjust html-mail content.
    'mode' : "html",
    'maillist' : tlist,
    'attname' : attname,
    'attbody' : attbody
    }
    try:
        response = requests.get(mail_url,params=mail_Info)
        logstr.log_info('send mail success')
    except Exception as e:
        logstr.log_info("Send Mail ERROR. %s" % (e))
template_mail = """<html><head><style type="text/css">table{border-collapse:collapse;margin:0 auto;text-align:center;}table td,table th{border:1px solid #cad9ea;color:#666;height:30px;}table thead th{background-color:#CCE8EB;width:100px;}table tr:nth-child(odd){background:#fff;}table tr:nth-child(even){background:#F5FAFA;}</style></head><table width='90%' class='table'><thead><tr><th>ID</th><th>StartTime</th><th>EndTime</th><th>test_url</th><th>base_url</th><th>Finished</th><th>DiffNum</th><th>DiffRate(%)</th><th>Testtag</th><th>Detail</th></tr></thead>"""
temp_format = """<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><a href="http://frontqa.web.sjs.ted/fy_xmldetail?tasknum=%d">Detail</a></td></tr></table></body></html>"""
if __name__ == '__main__':
    logstr = logUtils.logutil(task_id)
    subpid = os.getpid()
    set_subpid(subpid,1)
    (test_url,base_url,queryip,queryuser,querypassw,querypath) = getInfoFromDb(task_id)
    filelist = getQueryFile(root_path)
    getDiff(root_path,filelist,task_id,base_url,test_url)
    # send result by mail
    db = pymysql.connect('10.134.110.163','root','Zhangjj@sogou123','sogotest')
    cursor = db.cursor()
    sql = "SELECT id,start_time,end_time,test_url,base_url,user,diffnum,finished,testtag FROM %s where id='%d'" % ('fanyi_fyxmldiff',task_id)
    cursor.execute(sql)
    (id,start_time,end_time,test_url,base_url,task_user,diffnum,finished,testtag) = cursor.fetchone()
    attname=''
    attbody=''
    tlist=list()
    tlist.append(task_user+'@Sogou-inc.com')
    title = '翻译XML自动化diff详情'
    result=0
    if finished!=0:
        result = round(float(diffnum)/float(finished)*100,2)
        mail_body = template_mail+ temp_format % (id,start_time,end_time,test_url,base_url,finished,diffnum,result,testtag,int(id))
    else:
        mail_body = template_mail+ temp_format % (id,start_time,end_time,test_url,base_url,finished,diffnum,'0',testtag,int(id))
    sendMail(title,mail_body,tlist,attname,attbody)
