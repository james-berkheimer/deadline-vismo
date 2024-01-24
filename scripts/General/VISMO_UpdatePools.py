import clr
import os.path
import os, shutil, glob
import time
import re
import sys, string
import subprocess

from System.IO import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

metaScriptDialog = None
scriptPath = None

def __main__():    
    global metaScriptDialog    
    priorityDoc = "\custom\Pool_Priorities.txt"
    root = "\\\\renderfarm8\DeadlineRepository8"
    docPath = root + priorityDoc    
    text_file = open(docPath, "r")
    priorityList = text_file.readlines()
    priorityList = [s.rstrip() for s in priorityList]
    existingPools = RepositoryUtils.GetPoolNames()
    slaveNames = RepositoryUtils.GetSlaveNames(True)
    
    
    ## Delete old pools from Repository
    for pool in existingPools:        
        if str(pool) != 'none':
            # print ("Deleting:", str(pool))
            RepositoryUtils.DeletePool(str(pool))
    
    ## Add Pools to Repository
    for pool in priorityList:
        try:
            # print ("Adding:", pool)
            RepositoryUtils.AddPool(pool)
        except:
            print ("Pool %s already exists" % (pool))        
        
    ## Set the slaves pool list
    for slave in slaveNames:
        RepositoryUtils.SetPoolsForSlave( slave, priorityList )
    

    
    