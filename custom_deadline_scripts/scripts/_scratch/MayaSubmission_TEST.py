import os.path
import os, shutil, glob
import time
import re
import sys, string
import subprocess

def __main__():    
    deadlinebin = os.environ['DEADLINE_PATH'].split(os.pathsep)
    deadlinebin = deadlinebin[0]
    deadlinecommand = deadlinebin +  "\\" + "deadlinecommand.exe"
    deadlinecommandbg = deadlinebin +  "\\" + "deadlinecommandbg.exe"
    
    # Call DeadlineCommand to launch the monitor script file.
    deadlinecmd = [deadlinecommand, '-getrepositoryroot']
    p = subprocess.Popen(deadlinecmd, stdout=subprocess.PIPE)
    root = p.stdout.read()
    root = root.rstrip()
    print ("Root: " + root)
    # script = root + "\custom\scripts\Submission\VISMO_MayaRenderSubmission_TEST.py"
    script = root + "\scripts\Submission\MayaSubmission.py"
    # script = "\\RenderFarm8\DeadlineRepository8\custom\scripts\Submission\Maya\VISMO_MayaRenderSubmission.py"
    # script = "\\RenderFarm8\DeadlineRepository8\custom\scripts\Submission\Modo\VISMO_ModoSubmission_D8.py"
    print ("Script: " + script)
    # sceneFileFull = "O:/Users/jBerkheimer/Clients/ProjectTest/Animation/ProjectTest_MAYA/scenes/ALPHA/ProjectTest_01/ProjectTest_01_v002_JB.mb"
    # frameRange = "1.0-75.0"
    # outputPath = "O:/Users/jBerkheimer/Clients/ProjectTest/Animation/frames/MAYA_ProjectTest/ALPHA/ProjectTest_01/ProjectTest_01_v002"
    # fileTypeBox = "EXR16"
    # projectCode = "ProjectTest"
    # projectPhase = "ALPHA"
    # mayaVersion = "2017"
    # frameSize = "640x480"
    # projectPath = "O:/Users/jBerkheimer/Clients/ProjectTest/Animation/ProjectTest_MAYA/"
    # cameraNamesString = " ,RenderCam_02,RenderCam_01"

    
    print script
    print deadlinebin
    print deadlinecommand
    print deadlinecommandbg
    
    
    # launchDeadline = [deadlinecommandbg, '-executescript', script, sceneFileFull, frameRange, outputPath, fileTypeBox, projectCode, projectPhase, mayaVersion, frameSize, projectPath, cameraNamesString]
    launchDeadline = [deadlinecommandbg, '-executescript', script]
    print launchDeadline
    process = subprocess.Popen(launchDeadline, stdout=subprocess.PIPE)
    
    # launchDeadline = [deadlinecommandbg, '-popupmessage', "Hello James"]
    # process = subprocess.Popen(launchDeadline, stdout=subprocess.PIPE)
    
    
__main__()
