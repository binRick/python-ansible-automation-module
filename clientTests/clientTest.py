#!/usr/bin/env python
import os, sys, json
sys.path.insert(0, '../callbacks')

from zzz_logAraModule import IncludeResult
from zzz_logAraModule import ansibleCallbackTools


act = ansibleCallbackTools()

comm = act.getPidComm(os.getpid())
print(comm)

datas = act.getDatas()
print(json.dumps(datas, indent=4, sort_keys=True))
