#!/usr/bin/python3
#encoding: utf-8

#oldata_local_path 线上down下来的data，在本地的存储绝对路径
#tdata_path 要做的软链位置，一般是服务下serverdata的位置
#newdata_path 需要替换或者增加文件的目录地址，如替换/data/base/abcd.lst,则填写data/base即可
import os,shutil
class MakeLink:
    oldata_local_path=''
    tdata_path=''
    newdata_path=''
    def __init__(self,oldata_local_path,tdata_path,newdata_path):
        self.oldata_local_path=oldata_local_path
        self.tdata_path=tdata_path
        self.newdata_path=newdata_path
    def makelink(self):
        print('oldata_local_path:',self.oldata_local_path)
        print('tdata_path:',self.tdata_path)
        print('newdata_path:',self.newdata_path)
        tpath_data_dir=self.tdata_path+"/data"
        if(os.path.exists(tpath_data_dir)):
            print('tpath_data_dir is exist')
            shutil.rmtree(tpath_data_dir)
        os.makedirs(self.tdata_path+'/'+self.newdata_path)
        
        dir_lst=list()
        if self.newdata_path[-1] == "/":
            dir_lst = self.newdata_path[:-1].split('/')
        else:
            dir_lst = self.newdata_path.split('/')
        print(dir_lst)
        #dir_lst=['data', 'base', 'nb']
        #newlst: ['data/', 'data/base/', 'data/base/nb/']
        newlst=list()
        for index,dir in enumerate(dir_lst):
            print(index,dir)
            newpath=''
            for i in range(index+1):
                newpath+=dir_lst[i]+"/"
            newlst.append(newpath)
        print('newlst:',newlst)

        for k,item in enumerate(newlst):
            for filename in os.listdir(self.oldata_local_path+'/'+item):
                if os.path.exists(self.tdata_path+"/"+item+filename)==False:
                    os.symlink(self.oldata_local_path+"/"+item+filename,self.tdata_path+"/"+item+filename)




if __name__ == '__main__':
    mklink = MakeLink('/search/summary_o/webqo','/search/odin/daemon/webqo/qo_test/QueryOptimizer','data/base/nb')
    mklink.makelink()
