#!/usr/bin/python
# coding=UTF-8
# author=zhangjj

import ConfigParser


class ConfReader:
    conffile = ""

    def __init__(self, filepath):
        self.conffile = filepath
        self.cfg = ConfigParser.ConfigParser()

    def _loadconf(self):
        cf = self.cfg.read(self.conffile)

    def getAllSec(self):
        'Get all sections in config file'
        try:
            self._loadconf()
            return self.cfg.sections()
        except Exception, e:
            return "Read section error", e

    def getOpt(self, section):
        'Get options under a known section'
        try:
            self._loadconf()
            return self.cfg.options(section)
        except Exception, e:
            return "Read option error", e

    def getAllOpt(self):
        'Get all options in config file,it is a list'
        allOpt = list()
        try:
            for sec in self.getAllSec():
                for opt in self.getOpt(sec):
                    allOpt.append(opt)
            return allOpt
        except Exception, e:
            return "Read all options error", e

    def getItem(self, section):
        'Get Items by a known section'
        try:
            self._loadconf()
            return dict(self.cfg.items(section))
        except Exception, e:
            return "Read Item error", e

    def getKey(self, section, key):
        'Get value by  given section and key'
        try:
            if section in self.getAllSec():
                allkey = self.getItem(section)
            else:
                return "Section is wrong"
            if key in allkey:
                return allkey[key]
            else:
                return "Key is wrong"
        except Exception, e:
            return "Read key error", e

    def setValue(self, section, key, value):
        try:
            if section in self.getAllSec() and key in self.getOpt(section):
                self.cfg.set(section, key, value)
                with open(self.conffile, 'w') as fw:
                    self.cfg.write(fw)
            else:
                return "section or key not exsits"
        except Exception, e:
            return "set error", e


if __name__ == '__main__':
    r = ConfReader('/search/odin/daemon/webqo/tools/sggp/web_qo.ini')
    #	a = r.getKey('web_qo','press_qps')
    #	print(a)
    r.setValue('web_qo', 'press_qps', '10000')
# a=r.getAllSec()
#	print a
