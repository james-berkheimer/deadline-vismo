import os.path
import os, shutil, glob
import time
import re
import sys, string
import subprocess

def __main__():    

    # Establish Deadline launch commands
    launch_script = "/custom/scripts/Submission/Maya/VISMO_MayaRenderSubmission.py"
    # launch_script = "\\custom\\scripts\\Submission\\Maya\\DEV_MayaRenderSubmission.py"
    deadlinebin = os.environ['DEADLINE_PATH'].split(os.pathsep)
    deadlinebin = deadlinebin[0]
    deadlinecommand = deadlinebin + "/" + "deadlinecommand.exe"
    deadlinecmd = [deadlinecommand, '-getrepositoryroot']

    # Make deadeline launch command
    deadlinecommandbg = deadlinebin + "/" + "deadlinecommandbg.exe"
    launch_script_path = os.getenv('DEADLINE_REPOSITORY') + launch_script
    print(deadlinebin)
    print(deadlinecommand)
    print(deadlinecommandbg)
    print(launch_script_path)
    
    ######################################################################
    
    # deadlinebin = os.environ['DEADLINE_PATH'].split(os.pathsep)
    # deadlinebin = deadlinebin[0]
    # deadlinecommand = deadlinebin +  "\\" + "deadlinecommand.exe"
    # deadlinecommandbg = deadlinebin +  "\\" + "deadlinecommandbg.exe"
    
    # Call DeadlineCommand to launch the monitor script file.
    # deadlinecmd = [deadlinecommand, '-getrepositoryroot']
    # p = subprocess.Popen(deadlinecmd, stdout=subprocess.PIPE)
    # root = p.stdout.read()
    # root = root.rstrip().decode("utf-8")
    # print (root)
    # print (type(root))
    # print ("Root: " + root)
    # # script = root + "\custom\scripts\Submission\VISMO_MayaRenderSubmission_TEST.py"
    # # script = root + "\scripts\Submission\MayaSubmission.py"
    # script = root + "custom\scripts\Submission\Maya\VISMO_MayaRenderSubmission.py"
    # # script = "\\RenderFarm8\DeadlineRepository8\custom\scripts\Submission\Maya\VISMO_MayaRenderSubmission.py"
    # # script = "\\RenderFarm8\DeadlineRepository8\custom\scripts\Submission\Modo\VISMO_ModoSubmission_D8.py"
    # print ("Script: " + script)
    sceneFileFull = "O:/Users/jBerkheimer/Clients/MayaTest/Animation/MayaTest_MAYA/scenes/MayaTest_01_v005_JB.mb"
    frameRange = "1.0-75.0"
    outputPath = "O:/Users/jBerkheimer/Clients/MayaTest/Animation/frames/MAYA_MayaTest/ALPHA/MayaTest_01/MayaTest_01_v005"
    fileTypeBox = "EXR16"
    projectCode = "MayaTest"
    projectPhase = "ALPHA"
    mayaVersion = "2022"
    frameSize = "640x480"
    projectPath = "O:/Users/jBerkheimer/Clients/MayaTest/Animation/MayaTest_MAYA/"
    cameraNamesString = "RenderCam"

    
    # print (script)
    # print (deadlinebin)
    # print (deadlinecommand)
    # print (deadlinecommandbg)
    
    
    launchDeadline = [deadlinecommandbg, '-executescript', launch_script_path, sceneFileFull, frameRange, outputPath, fileTypeBox, projectCode, projectPhase, mayaVersion, frameSize, projectPath, cameraNamesString]
    # launchDeadline = [deadlinecommandbg, '-executescript', script]
    print (launchDeadline)
    process = subprocess.Popen(launchDeadline, stdout=subprocess.PIPE)
    
    # launchDeadline = [deadlinecommandbg, '-popupmessage', "Hello James"]
    # process = subprocess.Popen(launchDeadline, stdout=subprocess.PIPE)
    
    
__main__()
