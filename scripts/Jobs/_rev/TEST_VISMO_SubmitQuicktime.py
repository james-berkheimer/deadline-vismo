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
    metaScriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/Quicktime/Quicktime.ico" ) )
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        metaScriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return
    
    print "Root directory: " + RepositoryUtils.GetRootDirectory()
    #scriptPath = Path.Combine( RepositoryUtils.GetScriptsDirectory(), "Submission/QuicktimeSubmission.py" )
    scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory(), "custom/scripts/Submission/Quicktime/VISMO_QuicktimeSubmission.py" )
    # scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory(), "custom/scripts/Submission/Quicktime/DEV_QuicktimeSubmission.py" )
    scriptPath = PathUtils.ToPlatformIndependentPath( scriptPath )

    fileCount = JobUtils.GetOutputFilenameCount(0)
    outputFilenames = []
    for i in range (fileCount):     
        outputFilenames.append(JobUtils.GetOutputFilename(0,i))
        
    for i in outputFilenames:
        print i
        

    outputFilenames_CPM = []
    for i in outputFilenames:
        outputFilenames_CPM.append(RepositoryUtils.CheckPathMapping( i, False ))
    outputFilenames = []
    for i in outputFilenames_CPM:
        outputFilenames.append(PathUtils.ToPlatformIndependentPath( i ))
        
    outputFilenamesString = ",".join( outputFilenames ) #this turns a list of strings into a single string, separating items with commas
    print outputFilenamesString
    
    
    # outputFilenames = JobUtils.GetFirstOutputFilename( 0 )    
    # outputFilenames = RepositoryUtils.CheckPathMapping( outputFilenames, False )
    # outputFilenames = PathUtils.ToPlatformIndependentPath( outputFilenames )
    
    user = ""    
    versionId = ""
    job = selectedJobs[0]    
    frameSize = "1-24"
    jobPool = job.Pool
    pluginType = job.PluginName
    projectPhase = "TEST"
    jobName = "Test Job"
    # jobNameInfo = jobName.split("_")
    pluginName = job.PluginName        
    userInitials = "JB"
    # jobDirectory = os.path.dirname(outputFilenames)
    jobDirectory = os.path.dirname(outputFilenames[0])
    shotName = "TestShot"        
    showName = "TestShow"  
    # QtDirectory = getMovieDirectory(jobDirectory, pluginType, shotName, showName)
    QtDirectory = jobDirectory + "\\QT\\"
    
    if projectPhase == "" and pluginType == "AfterEffects":
        projectPhase = getAEPhase(jobDirectory)
        
    print "Quicktime directory: " + QtDirectory
    arguments = (outputFilenamesString, userInitials, pluginName, jobName, QtDirectory, frameSize, projectPhase)   
    
    # Making QT directories
    makeMovieDirectory(QtDirectory)
    
    versionId = job.GetJobExtraInfoKeyValue( "VersionId" )
    if versionId != "":
        arguments = (outputFilenamesString, userInitials, pluginName, jobName, QtDirectory, frameSize, projectPhase, "EnableShotgun")

    print "------ Now calling DEV_QuicktimeSubmission.py ------"
    ClientUtils.ExecuteScript( scriptPath, arguments )

#################

# def getShotDirName(directory, pluginType):
#     shotName = ""
#     fileInfo = directory.split("\\")
#     if pluginType == "Modo":
#         shotName = fileInfo[-4]
#     if pluginType == "Nuke":
#         shotName = fileInfo[-2]
#     if pluginType == "AfterEffects":
#         tmp = False
#         for f in fileInfo:
#             if f == "movies":
#                 tmp = True
#         if tmp == False:
#             shotName = fileInfo[-2]
#         else:
#             shotName = fileInfo[-1]
#             
#     return shotName
    
def getMovieDirectory(directory, pluginType, shotName, showName):
    if pluginType == "Nuke":
        directory = directory[:-4]
        directory = directory.replace("frames", "movies") 
        
    if pluginType == "Modo":
        directory = directory.split(shotName,1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies") 
            
    if pluginType == "AfterEffects":
        #directory = makeAEPath(directory, showName, shotName)
        directory = directory.split(shotName,1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies") 
        
    return directory

def makeMovieDirectory(directory):
    print "Checking if directory exists: "
    dirCheck = os.path.exists(directory)    
    if dirCheck == False:
        print "Making Directories....." + directory
        os.makedirs(directory)
    else:
        print "Directory Already Exists"
    
# def makeAEPath(directory, showName, shotName):
#     fileInfo = directory.split("\\")
#     phase = fileInfo[-3]
#     tmp = False
#     for f in fileInfo:
#         if f == "movies":
#             tmp = True
#     if tmp == True:
#         newPhaseName = "AE_" + showName + "_" + phase
#         directory = directory.split("movies",1)[0] + "movies\\" + newPhaseName + "\\" + shotName + "\\"
#     else:
#         newPhaseName = phase
#         directory = directory.split("frames",1)[0] + "movies\\" + newPhaseName + "\\" + shotName + "\\"
#         
#     return directory

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
    
    

