import os, shutil
import subprocess
from datetime import datetime

from Deadline.Scripting import *
from Deadline.Jobs import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None


def logPublish(outputDir, publishDir):
    logfile = os.path.join(publishDir, '.log')
    timestamp = datetime.now()
    print("Logging: %s" % (outputDir))
    if os.path.isfile(logfile):
        fileopen = open(logfile, "a+")
        lines = fileopen.readlines()
        fileopen.write("\n" + str(timestamp) + " " + outputDir)
    else:
        fileopen = open(logfile, "w+")
        fileopen.write(str(timestamp) + " " + outputDir)
    fileopen.close()


def newPublish():
    # Query Deadline for info on selected jobs
    print("Query Deadline for info on selected jobs")
    selectedJobs = MonitorUtils.GetSelectedJobs()
    for job in selectedJobs:
        pluginInfoKeys = job.GetJobPluginInfoKeys()
        jobInfoKeys = job.GetJobInfoKeys()
        for key in jobInfoKeys:
            if key == "Plugin":
                if job.GetJobInfoKeyValue(key) != "Nuke":
                    exit()
            if key == "OutputDirectory0":
                outputDir = job.GetJobInfoKeyValue(key)
            if key == "OutputFilename0":
                filename = job.GetJobInfoKeyValue(key)
            if key == "Name":
                shotname = job.GetJobInfoKeyValue(key)
                shot = '_'.join(shotname.split('_')[0:2])
            if key == "Frames":
                frames = job.GetJobInfoKeyValue(key)
            if key == "ExtraInfo9":
                frameExtention = job.GetJobInfoKeyValue(key)

        # Check if Publish exists.  If not create it
        print("Check if Publish exists.")
        publishDir = '_'.join(("NK", shotname.split('_')[0], "PUBLISH"))
        publishDirPath = outputDir.split(
            "frames")[0] + "frames\\" + publishDir + "\\" + shot
        if not os.path.isdir(publishDirPath):
            print("Making Publish dir")
            os.makedirs(publishDirPath)

        # Check if log file exists.  If true, get last version published then append newest version
        print("Check if log file exists.")
        logPublish(outputDir, publishDirPath)

        # Move latest version into publish directory
        print("Move latest version into publish")
        for file in sorted(os.listdir(outputDir)):
            if file.endswith(frameExtention.lower()):
                version = outputDir.split("\\")[-1]
                src = os.path.join(outputDir, file)
                dest = os.path.join(publishDirPath,
                                    file.replace(version, "PUBLISH"))
                shutil.copyfile(src, dest)
    return shotname


def __main__():
    global scriptDialog
    scriptDialog = DeadlineScriptDialog()
    print("--- Start Publishng ---")
    shotname = newPublish()
    scriptDialog.ShowMessageBox(
        "Your frames for %s \n have been published" % shotname,
        "Publish Confirmation")
    print("--- End Publishng ---")
