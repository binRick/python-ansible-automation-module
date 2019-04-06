from __future__ import (absolute_import, division, print_function)
import itertools
import logging
import os
import warnings

from colorclass import Color

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
    CALLBACK_NAME = 'myModule'

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


    def d(self,s,o):
	print(Color('\n{autogreen}** '+str(s)+' **{/autogreen}\n'+str(o)+'\n\n'))

    def getDatas(self):
	_datas=[]
	
	_s={}
	_s['key']='uid'
	_s['value']=os.geteuid()
	_s['type']='text'
	_datas.append(_s)

	_s={}
	_s['key']='cwd'
	_s['value']=os.getcwd()
	_s['type']='text'
	_datas.append(_s)

	_s={}
	_s['key']='env'
	_s['value']=os.environ.copy()
	_s['type']='text'
#	_datas.append(_s)

#	print(os.environ.keys())


	if 'SSH_CONNECTION' in os.environ.keys():
	  _s={}
  	  _s['key']='ssh'
	  _s['value']=os.environ['SSH_CONNECTION']
	  _s['type']='text'
	  _datas.append(_s)

	  if len(os.environ['SSH_CONNECTION'].split(' ')) == 4:
	    _s={}
  	    _s['key']='ssh_src_host'
	    _s['value']=os.environ['SSH_CONNECTION'].split(' ')[1]
	    _s['type']='text'
	    _datas.append(_s)

	    #Extract other fields here


	if 'SSH_TTY' in os.environ.keys():
	  _s={}
  	  _s['key']='tty'
	  _s['value']=os.environ['SSH_TTY']
	  _s['type']='text'
	  _datas.append(_s)




	return _datas
    def v2_playbook_on_start(self, playbook):
        path = os.path.abspath(playbook._file_name)
	self.d('Playbook Started','')
	self.d('path', path)
	self.d('name', current_app._cache['playbook'])
	for _d in self.getDatas():
	  self.d('Logging Data', _d)
          data = models.Data(playbook_id=current_app._cache['playbook'],
			key=_d['key'],
			value=_d['value'],
			type=_d['type'])
	  db.session.add(data)
	  db.session.commit()
	return

	#print("**PB STARTED**")
	#print(Color('{autogreen}** Playbook Started **{/autogreen}'))
        # Potentially sanitize some user-specified keys
        for parameter in app.config['ARA_IGNORE_PARAMETERS']:
            if parameter in cli_options:
                msg = "Not saved by ARA as configured by ARA_IGNORE_PARAMETERS"
                cli_options[parameter] = msg


