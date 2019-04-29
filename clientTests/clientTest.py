#!/usr/bin/env python
import os, sys
sys.path.insert(0, '../callbacks')

from zzz_logAraModule import IncludeResult
from zzz_logAraModule import ansibleCallbackTools


act = ansibleCallbackTools()

comm = act.getPidComm(os.getpid())
print(comm)
