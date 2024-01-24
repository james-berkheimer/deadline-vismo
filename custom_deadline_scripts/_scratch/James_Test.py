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
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    if len(selectedJobs) > 1:
        metaScriptDialog.ShowMessageBox( "Only one job can be selected at a time.", "Multiple Jobs Selected" )
        return
    outputFilenameCount = JobUtils.GetOutputFilenameCount( 0 )
        
    for i in range( 0, outputFilenameCount ):
        print i
        outputFilename = JobUtils.GetOutputFilename( 0, i )
        print outputFilename

    if outputFilenameCount > 0:
        job = selectedJobs[0]
        jobPool = job.Pool
        pluginType = job.PluginName
        jobName = job.Name
        jobNameInfo = jobName.split("_")
        directory = os.path.dirname(outputFilename)
        shotName = getShotDirName(directory, pluginType)
        frameSize = job.ExtraInfo8
        showName = shotName.split('_', 1)[0]
        
        
        print "Job Name: " + str(job)
        print "Plugin Name: " + str(pluginType)
        print "Pool Name: " + str(jobPool)
        print "Frame Size: " + str(frameSize)
        print "Job Name: " + str(jobName)
        print "Shot Name: " + str(shotName)
        print "Show Name: " + str(showName)
        print "Output Directory: " + directory
        print "Old AE Path: " + makeAEPath(directory, showName, shotName)
     
     
    directory = getMovieDirectory(directory, pluginType, shotName, showName)
    print "Quicktime Directory: " + directory
    #makeMovieDirectory(directory)
    
def getShotDirName(directory, pluginType):
    shotName = ""
    fileInfo = directory.split("\\")
    if pluginType == "Modo":
        shotName = fileInfo[-4]
        print "Modo: " + str(shotName)
    if pluginType == "Nuke":
        shotName = fileInfo[-2]
        print "Nuke: " + shotName
    if pluginType == "AfterEffects":
        tmp = False
        for f in fileInfo:
            if f == "movies":
                tmp = True
        if tmp == False:
            shotName = fileInfo[-2]
            #print "AE 1: " + shotName
        else:
            shotName = fileInfo[-1]
            #print "AE 2: " + shotName
            
    return shotName
    
    
def makeMovieDirectory(directory):
    print "Checking if directory exists: "
    dirCheck = os.path.exists(directory)    
    if dirCheck == False:
        print "Making Directories....." + directory
        os.makedirs(directory)
    else:
        print "Directory Already Exists"
    

def getMovieDirectory(directory, pluginType, shotName, showName):
    if pluginType == "Nuke":
        #directory = directory[:-4]
        directory = directory.replace("frames", "movies") 
        
    if pluginType == "Modo":
        directory = directory.split(shotName,1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies") 
            
    if pluginType == "AfterEffects":
        directory = directory.split(shotName,1)[0] + shotName + "\\"
        directory = directory.replace("frames", "movies") 
        
    return directory
    
    
    
def makeAEPath(directory, showName, shotName):
    fileInfo = directory.split("\\")
    phase = fileInfo[-3]
    tmp = False
    for f in fileInfo:
        if f == "movies":
            tmp = True
    if tmp == True:
        newPhaseName = "AE_" + showName + "_" + phase
        directory = directory.split("movies",1)[0] + "movies\\" + newPhaseName + "\\" + shotName + "\\"
    else:
        newPhaseName = phase
        directory = directory.split("frames",1)[0] + "movies\\" + newPhaseName + "\\" + shotName + "\\"
        
    return directory
    
    

