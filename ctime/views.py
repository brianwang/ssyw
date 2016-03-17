#-*- coding:utf-8 -*-
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse
import mysql
import MySQLdb
import paramiko
import time
import ansible.runner
import sys
import json

def getIPAddress(serverDir):
	global hostIP
	try:
		conn = MySQLdb.connect(host='120.92.224.183',user='root',passwd='5aRW7x8gFGNUB0dt',db='gm')
		cursor = conn.cursor()
		cursor.execute("select hostIp from admin_assetInfo where portGroup1='%s' or portGroup2='%s' or portGroup3='%s' or portGroup4='%s' or portGroup5='%s' or portGroup6='%s'" %(serverDir,serverDir,serverDir,serverDir,serverDir,serverDir))
		try:
			hostIP = cursor.fetchone()[0]
		except Exception,e:
			hostIP = None 
		cursor.close()
		conn.close()
	except Exception,e:
		sys.exit(1)
	return hostIP

def remoteCmd(hostip,commands):
	username = 'root'
	password = 'fUuoy2kvlp9xGDaB'
	port = '59878'
	try:
		s = paramiko.SSHClient()
		#s.load_system_host_keys()
		s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
		#建立ssh连接
		s.connect(hostip,port,username,password)
		for m in commands:
			stdin,stdout,stderr = s.exec_command(m)
			#time.sleep(5)
			print stdout.read()
		s.close()
	except Exception,e:
		print "%s连接出错:%s" %(hostip,e)

def ansibleCmd(hostip,serverDir,option):
	option = option
	results = ansible.runner.Runner(
		pattern = '%s' %hostip,forks = 5,
		module_name = 'shell', module_args= 'cd /data/game/%s/server/bin/;sh serverOptions.sh all %s' %(serverDir,option),
	).run()
	if results is None:
		print "No host found"
		sys.exit(1)

def modifyTime(hostip,openTime,serverDir):
        results = ansible.runner.Runner(
                pattern = '%s' %hostip,forks=5,
                module_name = 'shell', module_args='sed -i "/^openTime=/copenTime=%s" /data/game/%s/server/conf/config.properties' %(openTime,serverDir)
        ).run()
        if results is None:
                print "No host found"
                sys.exit(1)

def updateGM(serverDir,openTime):
	serverName = serverDir
	strList = serverName.split("_")
	strList.insert(3,'log')
	logdbName = '_'.join(strList)
	openTime = openTime
	try:
		conn = MySQLdb.connect(host='120.92.224.183',user='root',passwd='5aRW7x8gFGNUB0dt',db='gm')
		cursor = conn.cursor()
		cursor.execute("update admin_servers set opentime='%s' where db='%s' and gmurl<>''" %(openTime,logdbName))
		cursor.close()
		conn.close()
	except Exception,e:
		print e

def is_valid_date(str):
	try:
		time.strptime(str,'%Y-%m-%d %H:%M:%S')
		return True
	except:
		return False


def ctime(request):
	serverDir = request.GET.get('serverdir','')
	if serverDir:
		r1 = '%s' % serverDir
	else:
		r1 = []
		return render(request, "ctime.html")
	openTime = request.GET.get('opentime','')
	if is_valid_date(openTime):
		r2 = '%s' % openTime
	else:
		r2 = []
		error = '开服时间有误'
		return render_to_response('ctime.html',{'error':error})
	configPath = '/data/game/%s/server/conf/config.properties' %serverDir
	commands = ['sed -i "/^openTime=/copenTime=%s" /data/game/%s/server/conf/config.properties' %(openTime,serverDir)]
	serverip = getIPAddress(serverDir)
	if serverip is not None:
		#停服
		ansibleCmd(serverip,serverDir,option='stop')
		#修改配置文件里的时间
		modifyTime(serverip,openTime,serverDir)
		#启动
		ansibleCmd(serverip,serverDir,option='start')
		#更新后台时间
		updateGM(serverDir,openTime)
		results = '%s:openTime has changed:%s' %(r1,r2)
		return render_to_response('ctime.html', {'results': results})
	else:
		results = "未找到此区所在服务器ip,可能是服务器名称错误"
		return render_to_response('ctime.html', {'results': results})

def controlServer(request):
	serverDir = request.GET.get('serverdir','')
	if serverDir:
		r1 = '%s' % serverDir
		serverip = getIPAddress(serverDir)
	else:
		r1 = []
		return render(request, "control.html")
	conName = request.GET.get('conName')
	if serverip is not None:
		if conName:
			ansibleCmd(serverip,serverDir,conName)
			if conName == 'start':
				results = '%s start success' % serverDir
			elif conName == 'stop':
				results = '%s stop success' % serverDir
			return render_to_response('control.html', {'results': results})
	else:
		results = "未找到此区所在服务器ip,可能是服务器名称错误"
		return render_to_response('control.html', {'results': results})

def index(request):
	return render(request, "index.html")

def getOperList():
        dbconfig={'host':'120.92.224.183',
        'port': 3306,
        'user':'root',
        'passwd':'5aRW7x8gFGNUB0dt',
        'db':'gm',
        'charset':'utf8'}
        operList = []

        db = mysql.MySQL(dbconfig)
        sql = "select name from admin_oper"
        db.query(sql)
        result = db.fetchAllRows()
        for row in result:
                for colum in row:
                        operList.append(colum)
        db.close()
        return operList

def getAllTable(oper):
        dbconfig={'host':'120.92.224.183',
        'port': 3306,
        'user':'root',
        'passwd':'5aRW7x8gFGNUB0dt',
        'db':'original_log_new',
        'charset':'utf8'}
        tableList = []

        db = mysql.MySQL(dbconfig)
        tableName='center_userlogin_' + oper + "%"
        wanName='center_userlogin_51wan'+"%"
        if oper == '51':
                sql = "select table_name from information_schema.tables where table_name like '%s' and table_name not like '%s'" %(tableName,wanName)
        else:
                sql = "show tables like '%s'" % tableName
        db.query(sql)
        result = db.fetchAllRows()
        for row in result:
                for colum in row:
                        tableList.append(colum)
        db.close
        return tableList

def toTimeStamp(dtime):
	timeStamp=''
	if is_valid_date(dtime):
		timeArray = time.strptime(dtime,"%Y-%m-%d %H:%M:%S")
		timeStamp=int(time.mktime(timeArray))
	return timeStamp

def gmBaobiao(request):
        dbconfig={'host':'120.92.224.183',
        'port': 3306,
        'user':'root',
        'passwd':'5aRW7x8gFGNUB0dt',
        'db':'original_log_new',
        'charset':'utf8'}
        db = mysql.MySQL(dbconfig)
	operList = []
	rDict = {}
	sTimeStamp = toTimeStamp(request.GET.get('starttime',''))
	if not sTimeStamp:
		return render(request, "gmBaobiao.html")
	oper = request.GET.get('oper','')
	if oper == 'all':
		operList = getOperList()
	elif oper == '':
		return render(request, "gmBaobiao.html")
	else:
		operList.append(oper)
        for oper in operList:
                sum = 0
                tableList = getAllTable(oper)
                for table in tableList:
                        sql = "select count(distinct(username)) from %s where time>=%s" % (table,sTimeStamp)
                        db.query(sql)
                        result = db.fetchAllRows()[0][0]
                        sum += result
		rDict[oper] = sum
                #print "%s:%s" %(oper,sum)
	#print rDict
        db.close()
	#print rDict
	return render_to_response('gmBaobiao.html',{'rDict':rDict})
