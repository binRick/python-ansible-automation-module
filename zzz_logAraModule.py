from __future__ import (absolute_import, division, print_function)
import itertools, logging, os, pwd, warnings
from ansible import __version__ as ansible_version
from ara import models
from ara.models import db
from ara.webapp import create_app
from datetime import datetime
from distutils.version import LooseVersion
from flask import current_app
from oslo_serialization import jsonutils

with warnings.catch_warnings():
    warnings.filterwarnings('ignore')
    from ansible.plugins.callback import CallbackBase

try:
    from ansible import context
    cli_options = {key: value for key, value in context.CLIARGS.items()}
except ImportError:
    try:
        from __main__ import cli
        cli_options = cli.options.__dict__
    except ImportError:
        cli_options = {}

app = create_app()


class IncludeResult(object):
    """
    This is used by the v2_playbook_on_include callback to synthesize a task
    result for calling log_task.
    """
    def __init__(self, host, path):
        self._host = host
        self._result = {'included_file': path}


class CallbackModule(CallbackBase):
    """
    Saves data from an Ansible run into a database
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'zzz_logAraModule'

    def __init__(self):
        super(CallbackModule, self).__init__()

        if not current_app:
            ctx = app.app_context()
            ctx.push()

        self.taskresult = None
        self.task = None
        self.play = None
        self.playbook = None
        self.stats = None
        self.loop_items = []

        self.play_counter = itertools.count()
        self.task_counter = itertools.count()


    def getOriginPid(self,pid):
	p=999;
	_p=999;
	while _p > 1:
		_p=self.getPpid(pid)
		if _p > 1:
			p=_p
	return p

    def getPpid(self,pid):
	f = open("/proc/"+str(pid)+"/stat")
	stat = f.read().split(' ')
	return stat[3]

    def d(self,s,o):
	print('\n{autogreen}** '+str(s)+' **{/autogreen}\n'+str(o)+'\n\n')

    def getDatas(self):
	_datas=[]
	
	_s={}
	_s['key']='EXECUTION_PID'
	_s['value']=str(os.getpid())
	_s['type']='text'
	_datas.append(_s)

	_s={}
	_s['key']='EXECUTION_PPID'
	_s['value']=self.getPpid(os.getpid())
	_s['type']='text'
	_datas.append(_s)

#	_s={}
#	_s['key']='EXECUTION_ORIGIN_PID'
#	_s['value']=self.getOriginPid(os.getpid())
#	_s['type']='text'
#	_datas.append(_s)

	_s={}
	_s['key']='EXECUTION_UID'
	_s['value']=os.geteuid()
	_s['type']='text'
	_datas.append(_s)

	_s={}
	_s['key']='EXECUTION_USER'
	_s['value']=pwd.getpwuid(os.geteuid())[0]
	_s['type']='text'
	_datas.append(_s)

	_s={}
	_s['key']='EXECUTION_CWD'
	_s['value']=os.getcwd()
	_s['type']='text'
	_datas.append(_s)

	_s={}
	_s['key']='EXECUTION_ENV'
	_s['value']=os.environ.copy()
	_s['type']='json'
#	_datas.append(_s)


	if 'SSH_CONNECTION' in os.environ.keys():

	  if len(os.environ['SSH_CONNECTION'].split(' ')) != 4:
	    _s={}
  	    _s['key']='EXECUTION_SSH'
	    _s['value']=os.environ['SSH_CONNECTION']
	    _s['type']='text'
	    _datas.append(_s)
	  else:
	    _s={}
  	    _s['key']='EXECUTION_SSH_CLIENT_HOST'
	    _s['value']=os.environ['SSH_CONNECTION'].split(' ')[0]
	    _s['type']='text'
	    _datas.append(_s)

            _s={}
            _s['key']='EXECUTION_SSH_CLIENT_PORT'
            _s['value']=os.environ['SSH_CONNECTION'].split(' ')[1]
            _s['type']='text'
            _datas.append(_s)

            _s={}
            _s['key']='EXECUTION_SSH_SERVER_HOST'
            _s['value']=os.environ['SSH_CONNECTION'].split(' ')[2]
            _s['type']='text'
            _datas.append(_s)

            _s={}
            _s['key']='EXECUTION_SSH_SERVER_PORT'
            _s['value']=os.environ['SSH_CONNECTION'].split(' ')[3]
            _s['type']='text'
            _datas.append(_s)


	if 'SSH_TTY' in os.environ.keys():
	  _s={}
  	  _s['key']='EXECUTION_TTY'
	  _s['value']=os.environ['SSH_TTY']
	  _s['type']='text'
	  _datas.append(_s)

	return _datas


    def v2_playbook_on_start(self, playbook):
        path = os.path.abspath(playbook._file_name)
#	print("Path={}".format(path))
#	print("pb={}".format(current_app._cache['playbook']))

	for _d in self.getDatas():
          data = models.Data(playbook_id=current_app._cache['playbook'],key=_d['key'],value=_d['value'],type=_d['type'])
	  db.session.add(data)
	  db.session.commit()
