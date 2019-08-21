from __future__ import (absolute_import, division, print_function)
import itertools, logging, os, pwd, warnings, sys, subprocess, psutil, datetime, json, tempfile, time
from git import Repo
from git import Git
from oslo_serialization import jsonutils
from ansible import __version__ as ansible_version

from os.path import basename
from ansible import constants as C
from ansible import context
from ansible.module_utils._text import to_text
from ansible.utils.color import colorize, hostcolor
from ansible.plugins.callback.default import CallbackModule as CallbackModule_default

log = logging.getLogger('[MES-CFM]')

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


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'zzz_cfm'

    def __init__(self):
        super(CallbackModule, self).__init__()
	pass

	for requiredKey in ['CFM_PUB_DEPLOY_KEY_BASE64','CFM_GIT_REPO','CFM_GIT_REPO_BASE_PATH']:
		if not requiredKey in os.environ.keys():
			print("Missing Environment Variable {}".format(requiredKey))
			print("  Present env vars:  {}".format(", ".join*os.environ.keys()))
			sys.exit(1)

	self.CFM_GIT_REPO = os.environ['CFM_GIT_REPO']
	self.CFM_GIT_REPO_BASE_PATH = os.environ['CFM_GIT_REPO_BASE_PATH']
	self.CFM_PUB_DEPLOY_KEY_BASE64 = os.environ['CFM_PUB_DEPLOY_KEY_BASE64']

    def v2_playbook_on_task_start(self, task, is_conditional):
	#print("[MES-CFM] :: TASK STARTED => {} => {} :: action {}, \nattributes: {}\n args: {}\n diff: {}\n".format(task.get_name(), task._uuid, task.action, ", ".join(task._attributes.keys()), task._attributes['args'], task._attributes['diff']))
	if task.action == 'template':
		print("SAVING TEMPLATE")	

    def v2_runner_on_ok(self, result, msg="ok", display_color=C.COLOR_OK):
	#print("[MES-CFM] :: TASK OK")
	#print(result._result)

        if 'changed' in result._result and result._result['changed'] and task.action == 'template':
		print("[MES-CFM] :: TEMPLATE TASK CHANGED")
		
    def v2_playbook_on_start(self, playbook):
	PRIVATE_KEY_PATH = '~/.ssh/id_rsa_cfm'
	GIT_PATH = 'ssh://git@gitlab.product.healthinteractive.net/rblundell/mes-configuration-management'
	GIT_SSH_IDENTITY_FILE = os.path.expanduser(PRIVATE_KEY_PATH)
	GIT_SSH_CMD = 'ssh -i {}'.format(GIT_SSH_IDENTITY_FILE)
	GIT_BRANCH = 'master'
	GIT_ENV = {"GIT_SSH_COMMAND": GIT_SSH_CMD}
	GIT_CLONE_DIR = tempfile.mkdtemp()
	COMMIT_MSG = 'automated commit'
	if not os.path.exists(GIT_CLONE_DIR):
	    os.makedirs(GIT_CLONE_DIR)

	print("[MES-CFM] :: PLAYBOOK STARTED")
	print("GIT_PATH = {}".format(GIT_PATH))
	print("GIT_CLONE_DIR = {}".format(GIT_CLONE_DIR))
	print("GIT_BRANCH = {}".format(GIT_BRANCH))
	print("GIT_ENV = {}".format(GIT_ENV))

	repo = Repo.clone_from(GIT_PATH, GIT_CLONE_DIR, branch=GIT_BRANCH)

	#print("repo={}".format(repo))
	g = Git(repo.working_dir)
	g.checkout(GIT_BRANCH)
	changedFiles = [ item.a_path for item in repo.index.diff(None) ]
	#print("{} changedFiles: {}".format(len(changedFiles),changedFiles))
	commits = list(repo.iter_commits(GIT_BRANCH))
	latestCommitID = commits[0]
	#print("{} commits".format(len(commits)))
	latestCommit = repo.commit(latestCommitID)
	latestCommitFiles = list(latestCommit.tree.traverse())
	commitFiles = latestCommit.stats.files.keys()
	
	"""
	print("latestCommit: {}".format(latestCommit))
	print("{} latestCommitFiles: {}".format(len(latestCommitFiles), latestCommitFiles))
	print("{} latestCommit files: {}".format(len(commitFiles), ", ".join(commitFiles)))
	print("latestCommit total: {}".format(latestCommit.stats.total))
	print("{} latestCommit files: {}".format(len(latestCommit.stats.files), latestCommit.stats.files))
	"""

	"""
	file_count = 0
	files = []
	tree_count = 0
	for item in latestCommit.tree.traverse():
	    file_count += item.type == 'blob'
 	    files.append(item)  
	    tree_count += item.type == 'tree'
	print("file_count={}".format(file_count))
	print("tree_count={}".format(tree_count))
	print("files={}".format(files))
	"""

	commitFiles = {}

	for C in list(repo.iter_commits()):
	    commitFiles[C] = []
	    for f in C.stats.files.keys():
	    	commitFiles[C].append(f)
	print(commitFiles)

	tfile='tf2.txt'
	with open("{}/{}".format(GIT_CLONE_DIR,tfile), 'w') as fd:
		fd.write(str(time.time()))
    	repo.git.add(tfile)
	"""
        for file in repo.untracked_files:
            print('Adding untracked file: {}'.format(file))
	    repo.git.add(file)
	"""
	repo.index.commit(COMMIT_MSG)
	pr = repo.git.push('origin', GIT_BRANCH)
	print("push result: {}".format(pr))
