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
    
    # slaveNames = RepositoryUtils.GetSlaveNames(True)
    # for name in slaveNames:
    #     print name
        
    selectedSlaveNames = MonitorUtils.GetSelectedSlaveNames()
    for name in selectedSlaveNames:
        print name
        SlaveUtils.SendRemoteCommand(name, "OnLastTaskComplete StopSlave")
        
    selectedSlaveInfoSettings = MonitorUtils.GetSelectedSlaveInfoSettings()
    print selectedSlaveInfoSettings
    
    