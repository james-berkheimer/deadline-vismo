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

newPools = ["_ALEST_",
            "_PFIIN_",
            "_AVAVP_",
            "_DEPCA_",
            "_SAGGA_"]
            # "RELVE",
            # "OTSSG",
            # "BAXPE",
            # "BAXTI"


def __main__():
    global metaScriptDialog
    
    print RepositoryUtils.GetPoolNames()
    
    for pool in newPools:
        print pool
        # RepositoryUtils.AddPool(pool)
        
    for pool in newPools:
        print pool
        # RepositoryUtils.DeletePool(pool)
        
    # slaveNames = MonitorUtils.GetSelectedSlaveNames()
    slaveNames = RepositoryUtils.GetSlaveNames(True)
    for name in slaveNames:
        print name
        # RepositoryUtils.SetPoolsForSlave( name, newPools )
        # slavePools = RepositoryUtils.GetSlaveInfoSettings(name, True)
        # for pool in slavePools:
                # print pool
        
    # slaveNames = RepositoryUtils.GetSlaveNames(True)    
    # for name in slaveNames:
    #     print name
        
    # for pool in newPools:
    #     RepositoryUtils.AddPool(pool)
    #     RepositoryUtils.SetPoolsForSlave( slaveName, poolNames )
    # 
    # selectedSlaveInfoSettings = MonitorUtils.GetSelectedSlaveInfoSettings()
    # print selectedSlaveInfoSettings
    
    