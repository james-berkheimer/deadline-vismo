import os
import subprocess

from System.IO import *
from Deadline.Scripting import *
from Deadline.Jobs import *

modoEXE_14_1_1 = "C:\\Program Files\\Foundry\Modo\\14.1v1\\modo.exe"
modoEXE_13_2_1 = "C:\\Program Files\\Foundry\Modo\\13.2v1\\modo.exe"
modoEXE_11_2_1 = "C:\\Program Files\\Foundry\Modo\\11.2v1\\modo.exe"
modoEXE_12_1_2 = "C:\\Program Files\\Foundry\Modo\\12.1v2\\modo.exe"
modoEXE_2018 = "C:\\Program Files\\Autodesk\\Maya2018\\bin\\maya.exe"
modoEXE_2020 = "C:\\Program Files\\Autodesk\\Maya2020\\bin\\maya.exe"
nukeEXE_10_4 = "C:\\Program Files\\Nuke10.0v4\\Nuke10.0.exe"


def __main__():
    print("----")
    sceneFile = ""
    version = ""
    selectedJobs = MonitorUtils.GetSelectedJobs()
    for job in selectedJobs:
        print 'got:', job
        pluginInfoKeys = job.GetJobPluginInfoKeys()
        for key in pluginInfoKeys:
            # print key
            if key == "SceneFile":
                sceneFile = job.GetJobPluginInfoKeyValue(key)
            if key == "Version":
                version = job.GetJobPluginInfoKeyValue(key)

    fileType = sceneFile.split('.')[-1]
    print fileType
    if fileType == "lxo":
        if version == "11xx":
            cmd = [modoEXE_11_2_1, '-executescript', sceneFile]
            print cmd
        if version == "12xx":
            cmd = [modoEXE_12_1_2, '-executescript', sceneFile]
            print cmd
        if version == "13xx":
            cmd = [modoEXE_13_2_1, '-executescript', sceneFile]
            print cmd
        if version == "14xx":
            cmd = [modoEXE_14_1_1, '-executescript', sceneFile]
            print cmd
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    if fileType == "nk":
        cmd = [nukeEXE_10_4, '-executescript', sceneFile]
        print cmd
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)

    if fileType == "ma" or fileType == "mb":
        if version == "2018":
            cmd = [modoEXE_2018, '-file', sceneFile]
            print cmd
        if version == "2020":
            cmd = [modoEXE_2020, '-file', sceneFile]
            print cmd
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
