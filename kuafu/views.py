#coding:utf-8
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.http import StreamingHttpResponse
#from somewhere import handle_uploaded_file

from ctime.views import *
import MySQLdb
import paramiko
import ansible.runner
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
import os
from ctime.mysql import *

def controlOpsKF(conName):
	hostip = '120.92.232.1'
	results = ansible.runner.Runner(
		pattern = '%s' % hostip, forks = 5,
		module_name = 'shell', module_args = 'cd /data/game/kfmanager; sh %s.sh' % conName
	).run()
	if results is None:
		return render(request, "kuafu.html")

def cleanOpsDb():
        dbconfig={'host':'120.92.232.1',
        'port': 3306,
        'user':'root',
        'passwd':'5aRW7x8gFGNUB0dt',
        'db':'cqss_kf_new',
        'charset':'utf8'}
	tableList = []
	db = mysql.MySQL(dbconfig)
	db.query("show tables")
	result = db.fetchAllRows()
	for row in result:
		for colum in row:
			tableList.append(colum)
	tableList.remove('c_server')
	for t in tableList:
		sql = 'truncate table %s' %t
		db.update(sql) 
	db.close()

def cleanGamedb():
	hostip = '120.92.232.1'
	results = ansible.runner.Runner(
		pattern = '%s' % hostip, forks = 5,
		module_name = 'shell', module_args = 'cd /data/script/cleanBattleDate; sh clean_gameKF.sh'
	).run()
	if results is None:
		return render(request, "kuafu.html")

def reloadCfg(hostip,serverdir):
        results = ansible.runner.Runner(
                pattern = '%s' % hostip, forks = 5,
                module_name = 'shell', module_args = 'cd %s; sh reloadCfg.sh 1' % serverdir
        ).run()
	if results is None:
		return HttpResponse('热加载失败')

def getUnion(step):
        dbconfig={'host':'120.92.232.1',
        'port': 3306,
        'user':'root',
        'passwd':'5aRW7x8gFGNUB0dt',
        'db':'cqss_kf_new',
        'charset':'utf8'}
        db = mysql.MySQL(dbconfig)
        sql = 'select * from c_union where step=%s and signUp=1' % step
        db.query(sql)
        result = db.fetchAllRows()
	u_name='/data/ssyw/download/union.txt'
        with open(u_name,'w') as file:
                for row in result:
                        s_row = ','.join(["'%s'" % c for c in row]).replace('\'','')
                        file.write(s_row)
                        file.write('\n')
	db.close()
	return u_name

def handle_uploaded_file(f):
        file_name = ""
        try:
                path='/data/ssyw/upload/kuafu/'
                if not os.path.exists(path):
                        os.makedirs(path)
                file_name = path+f.name
                with open(file_name, 'wb+') as destination:
                     	for chunk in f.chunks():
                               	destination.write(chunk)
                        #destination.close()
        except Exception,e:
                print e
        return f

def file_download(request):
	step = request.POST.get('step')
	def file_iterator(file_name, chunk_size=512):
		with open(file_name) as file:
			while True:
				c = file.read(chunk_size)
				if c:
					yield c
				else:
					break
        if step:
                the_file_name = getUnion(step)
		response = StreamingHttpResponse(file_iterator(the_file_name))
		response['Content-Type'] = 'application/octet-stream'
		response['Content-Disposition'] = 'attachment;filename=%s' % os.path.basename(the_file_name)

		return response
	return render_to_response('download.html', locals(), context_instance=RequestContext(request))


@csrf_exempt
@csrf_protect
def update_file(request):
	src = ""
	dest = ""
	option = ""
	hostip = ""
	optionList = []
	render(request, 'kuafu.html')
	if request.method == 'POST':
		f = handle_uploaded_file(request.FILES.get('file',None))
		if f is None:
			return HttpResponse('nofile upload')
		src = '/data/ssyw/upload/kuafu/'+f.name
		optionList = request.POST.getlist('option')
	if optionList:
		for option in optionList:
			if option == 'ops':
				dest = '/data/game/kfmanager/data/'
				hostip = '120.92.232.1'
			elif option == 'client':
				dest = '/data/game/kuafu/client/assets/data/'
				hostip = '119.29.138.253'
			elif option == 'server':
				for dir in ['s9994','s9995','s9997','s9998']:
					serverdir = '/data/game/%s/server' % dir
					dest = serverdir + '/data/' 
					bindir = serverdir + '/bin/'
					hostip = '119.29.138.253'
					results = ansible.runner.Runner(
						pattern = '%s' % hostip, forks = 5,
						module_name = 'copy', module_args = 'src=%s dest=%s' %(src,dest)
					).run()
					reloadCfg(hostip,bindir)
			if src and dest and hostip and option != 'server':
				print option
        			results = ansible.runner.Runner(
                			pattern = '%s' % hostip, forks = 5,
                			module_name = 'copy', module_args = 'src=%s dest=%s' %(src,dest)
        			).run()
				if option == 'ops':
					controlOpsKF(conName='stop')
					controlOpsKF(conName='start')
		return HttpResponse('更新成功')

	conName = request.GET.get('conName')
	#if conName:
	#	controlOpsKF(conName)	
	if conName == 'clean':
		controlOpsKF(conName='stop')
		cleanOpsDb()	
		controlOpsKF(conName='start')
	else:
		controlOpsKF(conName)

	gameC = request.GET.get('gameC')
	if gameC: 
		cleanGamedb()	

	return render_to_response('kuafu.html',context_instance=RequestContext(request))
