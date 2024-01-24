import os, shutil
import subprocess

from Deadline.Scripting import *
from Deadline.Jobs import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None


def __main__():
    global scriptDialog
    shotname = "NukeTest_04_v004_JB"
    print("--- Start Publishng ---")
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.ShowMessageBox(
        "Your frames for %s \n have been published" % shotname,
        "Publish Confirmation")
    print("--- End Publishng ---")
