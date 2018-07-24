from optparse import OptionParser
import os,sys,io,urllib


import logging

from lib import TextFileUtils
from lib import LogUtils

L = logging 

def nl2br(str):
    if(type(str) is bytes):
        print ("[INFO]try to nl2br...")
        try:
            str = str.decode("utf-8")
        except UnicodeDecodeError:
            print ("[WARNING]cannot be decode by utf-8, trying gbk...")
            str = str.decode("gbk")
    return str.replace("\n", "<br />")

def getBody(filename, myEncoding = 'utf-8'):
    content = 'null'
    f=open(filename, 'r', encoding=myEncoding)
    if None !=f :
        content = f.read()
        f.close()
    return content

def sendSimpleMail(title, body, tlist, name):
    filepath = TextFileUtils.write_temp_file(body)
    sendMail(title,filepath,tlist,name)
    
def sendMail(title,body,tlist, name = "F2A Autotest", attachment = "" , use_nl2br = True):
        
    action = "http://mail.portal.sogou/portal/tools/send_mail.php"
    
    attname = ""
    attbody = ""
    
    if(not os.path.isfile(body)):
        LogUtils.sglog ("[Sendmail] cannot find body" + body, 4)
        return False
    
    LogUtils.sglog ("[Sendmail]content load from:" + body + ", size:" + str(os.path.getsize(body)))#update for attachments.
    if(len(attachment) > 0):
        if(not os.path.isfile(attachment)):
            LogUtils.sglog ("[Sendmail]cannot find attachment" + attachment, 4)
        else:
            LogUtils.sglog ("[Sendmail]load attachment from " + attachment + " ..., size:" + str(os.path.getsize(attachment)))
            attname = os.path.basename(attachment)
            attbody = TextFileUtils.read_file_intostr(attachment)

    send_body = getBody(body)
    if(use_nl2br):
        send_body = nl2br(send_body)
    dict_param = {
    'uid' : "chenchen@sogou-inc.com",
    'fr_name' : name,
    'fr_addr' : "chenchen@sogou-inc.com",
    'title' : title,
    'body' : send_body, #use nl2br to adjust html-mail content.
    'mode' : "html",
    'maillist' : tlist,
    'attname' : attname,
    'attbody' : attbody
    }
    try: 
        #the mail only support of gbk...
        try:
            url_param = urllib.parse.urlencode(dict_param, "ignore", encoding="gbk")
        except Exception as e:
            LogUtils.sglog ("mail content file might not gbk... try utf-8.")
            url_param = urllib.parse.urlencode(dict_param, "ignore", encoding="utf-8")
        url_param = url_param.encode('utf-8')
        #debug
        LogUtils.sglog ("size of url_param is:" + str(len(url_param)),0)
        response = urllib.request.urlopen(action,url_param)  
        response.close()
        LogUtils.sglog('send mail success')
    except Exception as e:
        L.error("Send Mail ERROR. %s" % (e))
        
if  '__main__' == __name__:
    ctitle = "cctitle"
    cfile = "./bodyfile"
    ctlist = "zhangjingjun@sogou-inc.com;"
    cname = "chenchen"
    sendMail(ctitle,cfile,ctlist,cname)


