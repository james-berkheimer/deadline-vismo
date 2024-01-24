import clr
import sys
import subprocess
import os.path

from System.IO import *
from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

metaScriptDialog = None
scriptPath = None


def __main__():
    global metaScriptDialog
    global scriptPath

    metaScriptDialog = DeadlineScriptDialog()

    metaScriptDialog.SetIcon(
        Path.Combine(RepositoryUtils.GetRootDirectory(),"custom/plugins/FFmpeg/FFmpeg.ico"))

    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        metaScriptDialog.ShowMessageBox(
            "Only one job can be selected at a time.",
            "Multiple Jobs Selected")
        return

    print("Root directory: %s" % RepositoryUtils.GetRootDirectory())
    scriptPath = Path.Combine(RepositoryUtils.GetRootDirectory(),"custom/scripts/Submission/FFmpeg/VISMO_FFmpegSubmission.py")
    scriptPath = PathUtils.ToPlatformIndependentPath(scriptPath)

    fileCount = JobUtils.GetOutputFilenameCount(0)
    outputFilenames = []
    for i in range(fileCount):
        outputFilenames.append(JobUtils.GetOutputFilename(0, i))

    outputFilenames_CPM = []
    for i in outputFilenames:
        outputFilenames_CPM.append(RepositoryUtils.CheckPathMapping(i, False))
    outputFilenames = []
    for i in outputFilenames_CPM:
        outputFilenames.append(PathUtils.ToPlatformIndependentPath(i))

    #this turns a list of strings into a single string, separating items with commas
    outputFilenamesString = ",".join(outputFilenames)
    # print("outputFilenamesString: %s" % outputFilenamesString)

    user = ""
    versionId = ""
    job = selectedJobs[0]
    frameSize = job.ExtraInfo8
    frameList = job.FramesList
    jobPool = job.Pool
    pluginType = job.PluginName
    projectPhase = job.ExtraInfo7
    if job.GetJobPluginInfoKeyValue('PassGroup'):
        passNamesString = job.ExtraInfo5  
    else:
        passNamesString = ""
    jobName = job.Name
    print("jobNane: %s" % jobName)
    jobNameInfo = jobName.split("_")
    pluginName = job.PluginName
    userInitials = str(job)[-2:]
    jobDirectory = os.path.dirname(outputFilenames[0])
    shotName = getShotDirName(jobDirectory, pluginType)
    print("shotNane: %s" % shotName)
    showName = shotName.split('_', 1)[0]
    videoDirectory = getVideoDirectory(jobDirectory, pluginType, shotName, showName)

    if projectPhase == "" and pluginType == "AfterEffects":
        projectPhase = getAEPhase(jobDirectory)

    print("Video directory: " + videoDirectory)

    print("arguments:")
    print(outputFilenamesString)
    print(userInitials)
    print(pluginName)
    print(jobName)
    print(videoDirectory)
    print(frameSize)
    print(frameList)
    print(projectPhase)
    print(passNamesString)
    
    arguments = (outputFilenamesString, userInitials, pluginName, jobName,
                 videoDirectory, frameSize, frameList, projectPhase, passNamesString)

    # Making video directories
    makeVideoDirectory(videoDirectory)

    print("File Input: %s" % outputFilenamesString)
    print("File Output: %s" % outputFilenamesString)

    print("------ Now calling VISMO_FFMpegSubmission.py ------")
    print("scriptPath: %s" % scriptPath)
    print("arguments: %s" % ",".join(arguments))
    
    ClientUtils.ExecuteScript(scriptPath, arguments)


#################


def getShotDirName(directory, pluginType):
    shotName = ""
    fileInfo = directory.split("\\")
    if pluginType == "Modo":
        shotName = fileInfo[-4]
    if pluginType == "Nuke":
        shotName = fileInfo[-2]
    if pluginType == "AfterEffects":
        tmp = False
        for f in fileInfo:
            if f == "movies":
                tmp = True
        if tmp == False:
            shotName = fileInfo[-2]
        else:
            shotName = fileInfo[-1]
    if pluginType == "MayaBatch":
        shotName = fileInfo[-3]

    return shotName


def getVideoDirectory(directory, pluginType, shotName, showName):
    if pluginType == "Nuke":
        directory = directory[:-4]
        directory = directory.replace("frames", "movies")

    if pluginType == "Modo":
        directory = directory.split(shotName, 1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies")

    if pluginType == "AfterEffects":
        directory = directory.split(shotName, 1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies")

    if pluginType == "MayaBatch":
        directory = directory.split(shotName, 1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies")

    return directory


def makeVideoDirectory(directory):
    print "Checking if directory exists: "
    dirCheck = os.path.exists(directory)
    if dirCheck == False:
        print "Making Directories....." + directory
        os.makedirs(directory)
    else:
        print "Directory Already Exists"


def makeAEPath(directory, showName, shotName):
    fileInfo = directory.split("\\")
    phase = fileInfo[-3]
    tmp = False
    for f in fileInfo:
        if f == "movies":
            tmp = True
    if tmp == True:
        newPhaseName = "AE_" + showName + "_" + phase
        directory = directory.split(
            "movies",
            1)[0] + "movies\\" + newPhaseName + "\\" + shotName + "\\"
    else:
        newPhaseName = phase
        directory = directory.split(
            "frames",
            1)[0] + "movies\\" + newPhaseName + "\\" + shotName + "\\"

    return directory


def getAEPhase(directory):
    phase = ""
    if "ALPHA" in directory:
        phase = "ALPHA"

    if "BETA" in directory:
        phase = "BETA"

    if "FINAL" in directory:
        phase = "FINAL"

    if "DVLP" in directory:
        phase = "DVLP"

    return phase
