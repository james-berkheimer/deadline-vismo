import clr
import sys
import subprocess

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
    
#####
    print RepositoryUtils.GetRootDirectory()
    #scriptPath = Path.Combine( RepositoryUtils.GetScriptsDirectory(), "Submission/QuicktimeSubmission.py" )
    scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory(), "custom/scripts/Submission/Quicktime/VISMO_QuicktimeSubmission.py" )
    scriptPath = PathUtils.ToPlatformIndependentPath( scriptPath )
#####
    
    outputFilenameCount = JobUtils.GetOutputFilenameCount( 0 )
    
    user = ""
    
    versionId = ""
    if outputFilenameCount > 0:
        job = selectedJobs[0]
        
#####
        userInitials = str(job)[-2:]
        pluginName = job.PluginName
        jobName = job.Name
#####
        
        versionId = job.GetJobExtraInfoKeyValue( "VersionId" )
        if versionId != "":
            lines = []
            lines.append( "VersionId=%s" % versionId )
            
            if job.GetJobExtraInfoKeyValue( "EntityId" ) != "":
                lines.append( "EntityId=%s" % job.GetJobExtraInfoKeyValue( "EntityId" ) )
            if job.GetJobExtraInfoKeyValue( "EntityType" ) != "":
                lines.append( "EntityType=%s" % job.GetJobExtraInfoKeyValue( "EntityType" ) )
            if job.GetJobExtraInfoKeyValue( "ProjectId" ) != "":
                lines.append( "ProjectId=%s" % job.GetJobExtraInfoKeyValue( "ProjectId" ) )
            if job.GetJobExtraInfoKeyValue( "TaskId" ) != "":
                lines.append( "TaskId=%s" % job.GetJobExtraInfoKeyValue( "TaskId" ) )
                
            if job.JobExtraInfo0 != "":
                lines.append( "TaskName=%s" % job.JobExtraInfo0 )
            elif job.GetJobExtraInfoKeyValue( "TaskName" ) != "":
                lines.append( "TaskName=%s" % job.GetJobExtraInfoKeyValue( "TaskName" ) )
            
            if job.JobExtraInfo1 != "":
                lines.append( "ProjectName=%s" % job.JobExtraInfo1 )
            elif job.GetJobExtraInfoKeyValue( "ProjectName" ) != "":
                lines.append( "ProjectName=%s" % job.GetJobExtraInfoKeyValue( "ProjectName" ) )
            
            if job.JobExtraInfo2 != "":
                lines.append( "EntityName=%s" % job.JobExtraInfo2 )
            elif job.GetJobExtraInfoKeyValue( "EntityName" ) != "":
                lines.append( "EntityName=%s" % job.GetJobExtraInfoKeyValue( "EntityName" ) )
            
            if job.JobExtraInfo3 != "":
                lines.append( "VersionName=%s" % job.JobExtraInfo3 )
            elif job.GetJobExtraInfoKeyValue( "VersionName" ) != "":
                lines.append( "VersionName=%s" % job.GetJobExtraInfoKeyValue( "VersionName" ) )
            
            if job.JobExtraInfo4 != "":
                lines.append( "Description=%s" % job.JobExtraInfo4 )
            elif job.GetJobExtraInfoKeyValue( "Description" ) != "":
                lines.append( "Description=%s" % job.GetJobExtraInfoKeyValue( "Description" ) )
                
            if job.JobExtraInfo5 != "":
                lines.append( "UserName=%s" % job.JobExtraInfo5 )
            elif job.GetJobExtraInfoKeyValue( "UserName" ) != "":
                lines.append( "UserName=%s" % job.GetJobExtraInfoKeyValue( "UserName" ) )
            
            shotgunSettingsPath = Path.Combine( GetDeadlineSettingsPath(), "QuicktimeSettingsShotgun.ini" )
            File.WriteAllLines( shotgunSettingsPath, tuple(lines) )
    
    
    if outputFilenameCount > 1:
        dialogWidth = 600
        
        #metaScriptDialog.SetSize( dialogWidth, (outputFilenameCount * 32) + 100 )
        metaScriptDialog.AllowResizingDialog( False )
        metaScriptDialog.SetTitle( "Submit Quicktime Job To Deadline" )
        
        metaScriptDialog.AddGrid()
        metaScriptDialog.AddControlToGrid( "Label", "LabelControl", "Please select the output images to create Quicktimes for.", 0, 0 )
        for i in range( 0, outputFilenameCount ):
            outputFilename = JobUtils.GetOutputFilename( 0, i )
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            metaScriptDialog.AddSelectionControlToGrid( str(i), "CheckBoxControl", (i==0), Path.GetFileName( outputFilename ), i+1, 0 )
        metaScriptDialog.EndGrid()
        
        metaScriptDialog.AddGrid()
        metaScriptDialog.AddHorizontalSpacerToGrid( "DummyLabel1", 0, 0 )
        submitButton = metaScriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
        submitButton.ValueModified.connect(SubmitButtonPressed)
        closeButton = metaScriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
        closeButton.ValueModified.connect(CloseButtonPressed)
        metaScriptDialog.EndGrid()
        
        metaScriptDialog.ShowDialog( True )
    else:
        outputFilename = JobUtils.GetFirstOutputFilename( 0 )
        outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
        outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
        
        #arguments = (outputFilename,)
        arguments = (outputFilename, userInitials)
        if versionId != "":
            #arguments = (outputFilename, "EnableShotgun")
            arguments = (outputFilename, userInitials, "EnableShotgun")
        
        ClientUtils.ExecuteScript( scriptPath, arguments )

def CloseQuicktimeDialog():
    global metaScriptDialog
    metaScriptDialog.CloseDialog()

def CloseButtonPressed(*args):
    CloseQuicktimeDialog()
    
def SubmitButtonPressed(*args):
    global metaScriptDialog
    global scriptPath
    
    selectedJobs = MonitorUtils.GetSelectedJobs()
    job = selectedJobs[0]
    
    versionId = job.GetJobExtraInfoKeyValue( "VersionId" )
    
    outputFilenameCount = JobUtils.GetOutputFilenameCount( 0 )
    for i in range( 0, outputFilenameCount ):
        if bool(metaScriptDialog.GetValue( str(i) ) ):
            outputFilename = JobUtils.GetOutputFilename( 0, i )
            outputFilename = RepositoryUtils.CheckPathMapping( outputFilename, False )
            outputFilename = PathUtils.ToPlatformIndependentPath( outputFilename )
            
            #arguments = (outputFilename,)
            arguments = (outputFilename, userInitials)
            if versionId != "":
                #arguments = (outputFilename, "EnableShotgun")
                arguments = (outputFilename, userInitials, "EnableShotgun")
            
            ClientUtils.ExecuteScript( scriptPath, arguments )
    
    CloseQuicktimeDialog()
