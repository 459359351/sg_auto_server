#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
__title__ = ''
__author__ = 'zhangjingjun'
__mtime__ = '2018/5/30'
# ----------Dragon be here!----------
              ┏━┓      ┏━┓
            ┏━┛ ┻━━━━━━┛ ┻━━┓
            ┃       ━       ┃
            ┃  ━┳━┛   ┗━┳━  ┃
            ┃       ┻       ┃
            ┗━━━┓      ┏━━━━┛
                ┃      ┃神兽保佑
                ┃      ┃永无BUG！
                ┃      ┗━━━━━━━━━┓
                ┃                ┣━┓
                ┃                ┏━┛
                ┗━━┓ ┓ ┏━━━┳━┓ ┏━┛
                   ┃ ┫ ┫   ┃ ┫ ┫
                   ┗━┻━┛   ┗━┻━┛
"""
import threading
import sys
import time
from datetime import datetime
import multiprocessing
def analysis_ret(data_file):
	retList = list()
	bad_line = 0
	with open(data_file,'rb') as fr:
		for line in fr:
			if b'Sogou-Observer' in line:
				try:
					split_data = line.strip().split(b',ret=')[1].split(b',')[0]
					retList.append(int(split_data))
				except Exception as e:
					bad_line += 1
					continue
	haveret = 0
	noret = 0
	for item in retList:
		if item > 0 :
			haveret+=1
		elif item == 0:
			noret +=1
	retlen = len(retList)
	retavgNum = float(haveret)/retlen
	noretavgNum = float(noret)/retlen
	print('%-20s\t%s' %('Get ret num:',sum(retList)/retlen) + '\n' +
		  '%-20s\t%s' % ('Get ret rate:', retavgNum)+ '\n' +
		  '%-20s\t%.4f' % ('None ret rate:', noretavgNum)+ '\n'+
		  '%-20s\t%s' % ('Ret invalid line:',bad_line))


def analysis_cost(data_file):
	output=''
	costList = list()
	bad_line = 0
	with open(data_file,'rb') as fr:
		for line in fr:
			if b'Sogou-Observer' in line:
				try:
					split_data = line.strip().split(b',cost=')[1].split(b',')[0]
					costList.append(int(split_data))
				except Exception as e:
					bad_line += 1
					continue
	costlen = len(costList)
	avgNum = float(sum(costList))/costlen
	total_line = costlen+bad_line
	output += ("AvgCost: %s" % avgNum + '\n')
	output += ("Total line: %s" % total_line+'\n')
	output += ("Cost invalid line: %s" % bad_line+'\n')
	costList.sort()
	data_distribution={'a:0 - 10: ':0,'b:10 - 50: ':0,'c:50 - 100: ':0,'d:100 - 150: ':0,'e:150 - 200: ':0,'f:200 - 300: ':0,'g:300 - 500: ':0,'h:500 - 1000: ':0,'i:1000 - 2000: ':0,'j:2000 - 3000: ':0,'k:3000 - 5000: ':0,
			'l:5000 - 7500: ':0,'m:7500 - 10000: ':0,'n:10000 - 15000: ':0,'o:15000 - 20000: ':0,'p:20000 - 25000: ':0,'q:25000 - 30000: ':0,'r:30000 - 50000: ':0,'s:50000 - 100000: ':0,'t:>100000: ':0}
	key_list=['a:0 - 10: ','b:10 - 50: ','c:50 - 100: ','d:100 - 150: ','e:150 - 200: ','f:200 - 300: ','g:300 - 500: ','h:500 - 1000: ','i:1000 - 2000: ','j:2000 - 3000: ','k:3000 - 5000: ',
                        'l:5000 - 7500: ','m:7500 - 10000: ','n:10000 - 15000: ','o:15000 - 20000: ','p:20000 - 25000: ','q:25000 - 30000: ','r:30000 - 50000: ','s:50000 - 100000: ','t:>100000: ']
	for item in costList:
		if 0<item<=10:
			data_distribution['a:0 - 10: '] += 1
		elif 10<item<=50:
			data_distribution['b:10 - 50: '] += 1
		elif 50<item<=100:
			data_distribution['c:50 - 100: '] += 1
		elif 100<item<=150:
			data_distribution['d:100 - 150: '] += 1
		elif 150<item<=200:
			data_distribution['e:150 - 200: '] += 1
		elif 200<item<=300:
			data_distribution['f:200 - 300: '] += 1
		elif 300<item<=500:
			data_distribution['g:300 - 500: '] += 1
		elif 500<item<=1000:
			data_distribution['h:500 - 1000: '] += 1
		elif 1000<item<=2000:
			data_distribution['i:1000 - 2000: '] += 1
		elif 2000<item<=3000:
			data_distribution['j:2000 - 3000: '] += 1
		elif 3000<item<=5000:
			data_distribution['k:3000 - 5000: '] += 1
		elif 5000<item<=7500:
			data_distribution['l:5000 - 7500: '] += 1
		elif 7500<item<=10000:
			data_distribution['m:7500 - 10000: '] += 1
		elif 10000<item<=15000:
			data_distribution['n:10000 - 15000: '] += 1
		elif 15000<item<=20000:
			data_distribution['o:15000 - 20000: '] += 1
		elif 20000<item<=25000:
			data_distribution['p:20000 - 25000: '] += 1
		elif 25000<item<=30000:
			data_distribution['q:25000 - 30000: '] += 1
		elif 30000<item<=50000:
			data_distribution['r:30000 - 50000: '] += 1
		elif 50000<item<=100000:
			data_distribution['s:50000 - 100000: '] += 1
		elif item>100000:
			data_distribution['t:>100000: '] += 1

	for keys in key_list:
		if data_distribution[keys]!=0:
			output += ('%-20s\t%-10s\t%f%%' % (keys, data_distribution[keys], (float(data_distribution[keys]) / costlen * 100)) + '\n')

	print(output)


def get_now_time():
	return datetime.now().strftime('%m%d%H%M%S')

if __name__ == '__main__':
	if len(sys.argv) == 2:
		log_file = sys.argv[1]
		process_sub = []
		p1 =  multiprocessing.Process(target=analysis_cost,args=(log_file,))
		process_sub.append(p1)
		p2 =  multiprocessing.Process(target=analysis_ret,args=(log_file,))
		process_sub.append(p2)
		for item in process_sub:
			item.start()
	else:
		print('argv is wrong')
