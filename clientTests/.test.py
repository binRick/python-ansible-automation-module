#!/usr/bin/env python
import os
from zzz_logAraModule import CallbackModule
_C=CallbackModule()
originPid=_C.getOriginPid(os.getpid())

print("Starting")



print("pppid={}".format(_C.getPpid(os.getpid())))
print("getOriginPid={}".format(_C.getOriginPid(os.getpid())))
print("getOriginComm={}".format(_C.getPidComm(originPid)))


