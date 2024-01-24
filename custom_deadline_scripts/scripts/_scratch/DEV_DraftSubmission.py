#Python.NET
import os, sys, re, mimetypes, traceback

from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from Deadline.Jobs import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

scriptDialog = None
sgVersionId = None
settings = None
job = None

def __main__( *args ):
    global scriptDialog
    global settings
    
    dialogWidth = 550
    dialogHeight = 675
    labelWidth = 120
    controlWidth = 152
    tabWidth = dialogWidth
    tabHeight = dialogHeight - 50
    
    scriptDialog = DeadlineScriptDialog()
    #scriptDialog.SetSize( dialogWidth, dialogHeight )
    scriptDialog.SetTitle( "Submit Draft Job To Deadline" )
    scriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/Draft/Draft.ico" ) )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0 , "The name of your job.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0 ,  "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0 , "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0 , "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1)

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0 , "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0 , "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0 , "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0 , "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0 , "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0 , "If desired, you can automatically archive or delete the job when it completes.", False)
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2 , "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render.")
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "DraftOptionsSeparator", "SeparatorControl", "Draft Options", 0, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "ScriptLabel", "LabelControl", "Draft Template", 1, 0 , "The script file to be executed.", False )
    scriptDialog.AddSelectionControlToGrid( "ScriptBox", "FileBrowserControl", "", "Draft Scripts (*.py);;All Files (*)", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input File", 2, 0 , "The input file(s) on which to apply the Draft script.", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox", "FileBrowserControl", "", "All Files (*)", 2, 1, colSpan=2 )
    inputBox.ValueModified.connect(InputImagesModified)

    scriptDialog.AddControlToGrid( "OutputDirLabel", "LabelControl", "Output Folder", 3, 0 , "The output folder in which the Draft script should put output files.  Can be absolute, or relative to input folder.", False )
    scriptDialog.AddSelectionControlToGrid( "OutputDirBox", "FolderBrowserControl", "", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OutputFileLabel", "LabelControl", "Output File Name", 4, 0 , "The name that the script should use for the output file(s).", False )
    outputFileBox = scriptDialog.AddControlToGrid( "OutputFileBox", "TextControl", "", 4, 1, colSpan=2 )
    outputFileBox.ValueModified.connect(OutputFileModified)

    scriptDialog.AddControlToGrid( "FrameListLabel", "LabelControl", "Frame List", 5, 0 , "The list of Frames that  should be processed by the script.", False )
    scriptDialog.AddControlToGrid( "FrameListBox", "TextControl", "", 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "SGUploadBox", "CheckBoxControl", False, "Upload Output To Shotgun", 5, 2 , "If selected, output will be uploaded to Shotgun." )
    scriptDialog.SetEnabled( "SGUploadBox", False )

    scriptDialog.AddControlToGrid( "OptionalParametersSeparator", "SeparatorControl", "Optional Draft Parameters", 6, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "UserLabel", "LabelControl", "User", 7, 0 , "Optionally used to pass metadata to the Draft script.", False )
    scriptDialog.AddControlToGrid( "UserBox", "TextControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "EntityLabel", "LabelControl", "Entity", 8, 0 , "Optionally used to pass metadata to the Draft script.", False )
    scriptDialog.AddControlToGrid( "EntityBox", "TextControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 9, 0 , "Optionally used to pass metadata to the Draft script.", False )
    scriptDialog.AddControlToGrid( "VersionBox", "TextControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Additional Args", 10, 0 , "The arguments to pass to the script. If no extra arguments are required, leave this blank.", False )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 10, 1, colSpan=2 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "DummyLabel1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(CloseButtonPressed)
    scriptDialog.EndGrid()
    
    settings = ("DepartmentBox", "CategoryBox", "PoolBox","SecondaryPoolBox", "GroupBox", "PriorityBox", "IsBlacklistBox", "MachineListBox", "LimitGroupBox", "ArgsBox", "ScriptBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    LoadDefaults()
    
    scriptDialog.ShowDialog( False )

#This functions fills in default values based on the selected job
def LoadDefaults():
    global scriptDialog
    global sgVersionId
    global updatingInputFile
    global job
    
    job = MonitorUtils.GetSelectedJobs()[0]
    
    #check for shotgun
    if job.GetJobExtraInfoKeyValue( 'VersionId' ) != "" and job.ExtraInfo5 != "":
        sgVersionId = job.GetJobExtraInfoKeyValue( 'VersionId' )
        
        scriptDialog.SetValue( 'EntityBox', job.ExtraInfo2 )
        scriptDialog.SetValue( 'VersionBox', job.ExtraInfo3 )
        scriptDialog.SetValue( 'UserBox', job.ExtraInfo5 )
        
        if ( scriptDialog.GetValue( "OutputFileBox" ).strip() != "" ):
            scriptDialog.SetEnabled( 'SGUploadBox', True )
            scriptDialog.SetValue( 'SGUploadBox', True )
    else: 
        sgVersionId = None
        scriptDialog.SetValue( 'UserBox', job.UserName )
        scriptDialog.SetValue( 'EntityBox', job.Name )
    
    inputFile = ""
    outputDir = ""
    outputFile = ""
    if len(job.OutputDirectories) > 0:
        inputFile = job.OutputDirectories[0]
        inputFile = RepositoryUtils.CheckPathMapping( inputFile, False )
        inputFile = PathUtils.ToPlatformIndependentPath( inputFile )
        
        outputDir = os.path.join( inputFile, "Draft" )
        
        if len(job.OutputFileNames) > 0:
            inputFile = os.path.join( inputFile, job.OutputFileNames[0] )
            inputFile = re.sub( "\?", "#", inputFile )
            
            (tempFileName, oldExt) = os.path.splitext( job.OutputFileNames[0] )
            tempFileName = re.sub( "[\?#]", "", tempFileName ).rstrip( "_.- " )
            outputFile = tempFileName + ".mov"
            
    scriptDialog.SetValue( 'InputBox', inputFile )
    scriptDialog.SetValue( 'OutputDirBox', outputDir )
    scriptDialog.SetValue( 'OutputFileBox', outputFile )
    
    scriptDialog.SetValue( 'DependencyBox', job.JobId )
    frameList = FrameUtils.ToFrameString( job.Frames )
    scriptDialog.SetValue( 'FrameListBox', frameList )
    scriptDialog.SetValue( 'NameBox', job.Name + " [DRAFT]" )

def OutputFileModified(*args):
    global sgVersionId
    global scriptDialog
    
    outputFileName = scriptDialog.GetValue( "OutputFileBox" ).strip()
    enabled = outputFileName != "" and sgVersionId != None
    scriptDialog.SetEnabled( 'SGUploadBox', enabled )

def InputImagesModified(*args):
    try:
        fileName = scriptDialog.GetValue( "InputBox" )
        
        if fileName != "":
            #Get the base dir and the file name w/o extension
            (outputDir, outputFileName) = os.path.split( fileName )
            scriptDialog.SetValue( "OutputDirBox", os.path.join( outputDir, "Draft" ) )
            
            if os.path.isfile(fileName):
                (mimeType, _) = mimetypes.guess_type( fileName )
                
                if mimeType != None and mimeType.startswith( 'video' ):
                    #file seems to be a video, don't bother looking for padding
                    pass
                else:
                    #Assume it's an image sequence
                    frameRange = FrameUtils.GetFrameRangeFromFilename( fileName )
                    scriptDialog.SetValue( "FrameListBox", frameRange )
                    
                    (outputFileName, _) = os.path.splitext( FrameUtils.SubstituteFrameNumber( outputFileName, "" ) )
                    outputFileName = outputFileName.rstrip( "_.- " ) + ".mov" 
                
                    padding = '#' * FrameUtils.GetPaddingSizeFromFilename( fileName )
                    scriptDialog.SetValue( "InputBox",  FrameUtils.SubstituteFrameNumber( fileName, padding ) )
            
                scriptDialog.SetValue( "OutputFileBox", outputFileName )
    except:
        pass

def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "DraftSettings.ini" )

def CloseDialog():
    global scriptDialog
    global settings
    
    #scriptDialog.SaveSettings( GetSettingsFilename(), settings )
    scriptDialog.CloseDialog()
    
def CloseButtonPressed( * args ):
    CloseDialog()

def SubmitButtonPressed( *args ):
    global scriptDialog
    global job
    
    # Check if Draft files exist.
    sceneFile = scriptDialog.GetValue("ScriptBox")
    if ( sceneFile == "" ):
        scriptDialog.ShowMessageBox( "Please select a Draft Template.", "Error" )
        return
    elif( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox( "Cannot find Draft script '%s'" % sceneFile, "Error" )
        return
    elif( PathUtils.IsPathLocal( sceneFile ) ):
        result = scriptDialog.ShowMessageBox( "The Draft Template's location '%s' is local.\n\nAre you sure you want to continue?" % sceneFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    #Check for local paths
    inFile = scriptDialog.GetValue("InputBox")
    outputDirectory = scriptDialog.GetValue( "OutputDirBox" ).strip()
    if ( inFile == None or inFile.strip() == "" ):
        scriptDialog.ShowMessageBox( "Please specify input for the Draft script to process", "Error" )
        return
    elif ( PathUtils.IsPathLocal(inFile) ):
        result = scriptDialog.ShowMessageBox( "The input file location '%s' is local.\n\nAre you sure you want to continue?" % inFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    elif ( PathUtils.IsPathLocal( outputDirectory ) ):
        result = scriptDialog.ShowMessageBox( "The output directory '%s' is local.\n\nAre you sure you want to continue?" % inFile, "Warning", ("Yes","No") )
        if(result=="No"):
            return
    
    #Check if output directory exists
    if ( not Directory.Exists( outputDirectory ) ):
        result = scriptDialog.ShowMessageBox( "The selected output directory '%s' does not exist.\n\nDo you wish to create this directory now?" % outputDirectory, "Warning", ("Yes","No") )
        if ( result == "Yes" ):
            Directory.CreateDirectory( outputDirectory )
    
    #Check if a valid frame range has been specified
    frames = scriptDialog.GetValue( "FrameListBox" )
    if( not FrameUtils.FrameRangeValid( frames ) ):
        scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
        return
    
    if ( not "#" in inFile ):
        paddingString = ""
        for i in range( 0, FrameUtils.GetPaddingSizeFromFilename( inFile ) ):
            paddingString += "#"
        
        inFile = FrameUtils.SubstituteFrameNumber( inFile, paddingString )
    
    outputFile = Path.Combine( outputDirectory, scriptDialog.GetValue( "OutputFileBox" ).strip() )
    
    # Create job info file.
    jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "draft_job_info.job" )
    
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    try:
        writer.WriteLine( "Plugin=Draft" )
        writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
        writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
        writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
        writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
        writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
        writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
        writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
        writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
        writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
        writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
        writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
        
        #Assume we're making a quicktime, set a huge chunk size
        writer.WriteLine( "Frames=" + scriptDialog.GetValue( "FrameListBox" ) )
        writer.WriteLine( "ChunkSize=1000000" )
        writer.WriteLine( "MachineLimit=1" )
        writer.WriteLine( "OutputFilename0=%s\n" % outputFile )
        
        if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
            writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
        else:
            writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
        if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
            writer.WriteLine( "InitialStatus=Suspended" )

        if ( scriptDialog.GetValue("SGUploadBox") and scriptDialog.GetEnabled("SGUploadBox")  ):
            if sgVersionId != None:
                #Pull any SG info from the other job
                writer.WriteLine( "ExtraInfo0=%s\n" % job.ExtraInfo0 )
                writer.WriteLine( "ExtraInfo1=%s\n" % job.ExtraInfo1 )
                writer.WriteLine( "ExtraInfo2=%s\n" % job.ExtraInfo2 )
                writer.WriteLine( "ExtraInfo3=%s\n" % job.ExtraInfo3 )
                writer.WriteLine( "ExtraInfo4=%s\n" % job.ExtraInfo4 )
                writer.WriteLine( "ExtraInfo5=%s\n" % job.ExtraInfo5 )

                #Only bother with the necessary KVPs
                writer.WriteLine( "ExtraInfoKeyValue0=VersionId=%s\n" % sgVersionId )
                writer.WriteLine( "ExtraInfoKeyValue1=TaskId=%s\n" % job.GetJobExtraInfoKeyValue( 'TaskId' ) )
                writer.WriteLine( "ExtraInfoKeyValue2=Mode=UploadMovie\n" )
            else:
                scriptDialog.ShowMessageBox( "The 'Upload to Shotgun' option has been selected, but no Shotgun version has been found.", "Error" )
                return
    finally:
        writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "draft_plugin_info.job" )
    
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    try:
        #prep the script arguments
        args = []
        args.append( 'username="%s" ' % scriptDialog.GetValue( 'UserBox' ) )
        args.append( 'entity="%s" ' % scriptDialog.GetValue( 'EntityBox' ) )
        args.append( 'version="%s" ' % scriptDialog.GetValue( 'VersionBox' ) )
        
        args.append( 'inFile="%s" ' % inFile )
        args.append( 'outFolder="%s" ' % outputDirectory )
        args.append( 'outFile="%s" ' % outputFile )
        
        frames = FrameUtils.Parse( scriptDialog.GetValue( "FrameListBox" ) )
        if (frames != None and len(frames) > 0):
            args.append( 'startFrame=%s ' % frames[0] )
            args.append( 'endFrame=%s ' % frames[-1] )
        args.append( 'frameList="%s" ' % scriptDialog.GetValue( "FrameListBox" ) )
        
        args.append( 'deadlineJobID=%s ' % job.JobId )
        
        #remove spaces between equal signs and other text
        extraArgs = scriptDialog.GetValue( "ArgsBox" )
        regexStr = r"(\S*)\s*=\s*(\S*)"
        replStr = r"\1=\2"
        extraArgs = re.sub( regexStr, replStr, extraArgs )
        
        args.append( extraArgs )
        
        #write out the params to the file
        writer.WriteLine( "scriptFile=%s" % scriptDialog.GetValue( "ScriptBox" ) )
        i = 0
        for scriptArg in args:
            writer.WriteLine( "ScriptArg%d=%s" % ( i, scriptArg ) )
            i += 1
    finally:
        writer.Close()
        
    # Setup the command line arguments.
    arguments = StringCollection()
    arguments.Add( "-notify" )
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    
    # Now submit the job.
    ScriptUtils.ExecuteCommand( arguments )
    
    CloseDialog()
