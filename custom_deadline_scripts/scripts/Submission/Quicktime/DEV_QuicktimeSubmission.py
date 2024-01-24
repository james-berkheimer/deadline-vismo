import clr

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *
from Deadline.Plugins import *

from System.IO import File
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
presetSettings = None
startup = True
updatingOutputFile = False
shotgunSettings = {}
fTrackSettings = {}
IntegrationOptions = ["Shotgun","FTrack"]
fileSeqs = []
userInitials = ""
pluginName = ""
jobSceneName = ""
fileDirectory = ""
frameSize = ""
projectPhase = ""

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    global scriptDialog
    global settings
    global presetSettings
    global startup
    global fileSeqs
    global userInitials
    global pluginName
    global jobSceneName
    global fileDirectory
    global frameSize
    global projectPhase
    
#########################################################
    fileSeqs = args[0].split(",")
    for i in fileSeqs:
            print "File....................." + i           

    userInitials = args[1]
    pluginName = args[2]
    jobSceneName = args[3]
    fileDirectory = args[4]
    frameSize = args[5]
    projectPhase = args[6]
    print ("PROJECT PHASE IS__________________________" + projectPhase)
#########################################################
    
    dialogWidth = 600
    dialogHeight = 530
    labelWidth = 150
    controlWidth = 180
    
    tabHeight = 480
    tabWidth = dialogWidth - 16
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Quicktime Job To Deadline" )
    scriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/Quicktime/Quicktime.ico" ) )
    
    scriptDialog.AddTabControl("Job Options Tabs", dialogWidth+8, tabHeight)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "JobOptionsSeparator", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    # scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    # scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
    
###################################################
    scriptDialog.AddControlToGrid( "ProjectPhaseLabel", "LabelControl", "Project Phase", 5, 0, "The Project you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "ProjectPhaseBox", "TextControl", "", 5, 1 )
 
    scriptDialog.AddControlToGrid( "FrameSizeLabel", "LabelControl", "Frame Size", 6, 0, "The Project you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "FrameSizeBox", "TextControl", "", 6, 1 ) 
    
    scriptDialog.AddControlToGrid( "FileTypeLabel", "LabelControl", "File Type", 7, 0, "The Project you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "FileTypeBox", "TextControl", "", 7, 1 )
###################################################
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 1, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 1, 1 )

    # scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    # scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "quicktime", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 5, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 6, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 6, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 7, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 8, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 9, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 9, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 9, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Input sequnce", 0, 0, colSpan=4 )
###################################################
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images 01", 1, 0, "The frames you would like to generate the Quicktime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range accordingly. ", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox01", "FileBrowserControl", "", "All Files (*)", 1, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images 02", 2, 0, "The frames you would like to generate the Quicktime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range accordingly. ", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox02", "FileBrowserControl", "", "All Files (*)", 2, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images 03", 3, 0, "The frames you would like to generate the Quicktime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range accordingly. ", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox03", "FileBrowserControl", "", "All Files (*)", 3, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "InputLabel", "LabelControl", "Input Images 04", 4, 0, "The frames you would like to generate the Quicktime from. If a sequence of frames exist in the same folder, Deadline will automatically collect the range of the frames and will set the Frame Range accordingly. ", False )
    inputBox = scriptDialog.AddSelectionControlToGrid( "InputBox04", "FileBrowserControl", "", "All Files (*)", 4, 1, colSpan=3 )

    #inputBox.ValueModified.connect(InputImagesModified)
    
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Output Sequence", 5, 0, colSpan=4 )

    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Movie File", 6, 0, "The name of the Quicktime to be generated. ", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox01", "FileSaverControl", "", "All Files (*)", 6, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 7, 0, "The first frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox01", "RangeControl", 0, -1000000, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 7, 2, "The last frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox01", "RangeControl", 0, -1000000, 1000000, 0, 1, 7, 3 )
    ###
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Movie File", 8, 0, "The name of the Quicktime to be generated. ", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox02", "FileSaverControl", "", "All Files (*)", 8, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 9, 0, "The first frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox02", "RangeControl", 0, -1000000, 1000000, 0, 1, 9, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 9, 2, "The last frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox02", "RangeControl", 0, -1000000, 1000000, 0, 1, 9, 3 )
    ###
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Movie File", 10, 0, "The name of the Quicktime to be generated. ", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox03", "FileSaverControl", "", "All Files (*)", 10, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 11, 0, "The first frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox03", "RangeControl", 0, -1000000, 1000000, 0, 1, 11, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 11, 2, "The last frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox03", "RangeControl", 0, -1000000, 1000000, 0, 1, 11, 3 )
    ###
    scriptDialog.AddControlToGrid( "OutputLabel", "LabelControl", "Output Movie File", 12, 0, "The name of the Quicktime to be generated. ", False )
    scriptDialog.AddSelectionControlToGrid( "OutputBox04", "FileSaverControl", "", "All Files (*)", 12, 1, colSpan=3 )
    ##
    scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 13, 0, "The first frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "StartFrameBox04", "RangeControl", 0, -1000000, 1000000, 0, 1, 13, 1 )
    scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 13, 2, "The last frame of the input sequence.", False )
    scriptDialog.AddRangeControlToGrid( "EndFrameBox04", "RangeControl", 0, -1000000, 1000000, 0, 1, 13, 3 )
###################################################
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Quicktime Options", 1, 0, colSpan=4 )
    
    # scriptDialog.AddControlToGrid( "StartFrameLabel", "LabelControl", "Start Frame", 2, 0, "The first frame of the input sequence.", False )
    # scriptDialog.AddRangeControlToGrid( "StartFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 2, 1 )
    # scriptDialog.AddControlToGrid( "EndFrameLabel", "LabelControl", "End Frame", 2, 2, "The last frame of the input sequence.", False )
    # scriptDialog.AddRangeControlToGrid( "EndFrameBox", "RangeControl", 0, -1000000, 1000000, 0, 1, 2, 3 )

    scriptDialog.AddControlToGrid( "CodecLabel", "LabelControl", "Codec", 3, 0, "The codec format to use for the Quicktime. ", False )
    codecBox = scriptDialog.AddComboControlToGrid( "CodecBox", "ComboControl", "QuickTime Movie", ("3G","AVI","DV Stream","FLC","MPEG-4","QuickTime Movie"), 3, 1 )
    codecBox.ValueModified.connect(CodecChanged)
    scriptDialog.AddControlToGrid( "FrameRateLabel", "LabelControl", "Frame Rate", 3, 2, "The frame rate of the Quicktime. ", False )
    scriptDialog.AddRangeControlToGrid( "FrameRateBox", "RangeControl", 24.00, 0.01, 100.00, 2, 1.00, 3, 3 )

    # scriptDialog.AddControlToGrid( "AudioLabel", "LabelControl", "Audio File (Optional)", 4, 0, "Specify an audio file to be added to the Quicktime movie. Leave blank to disable this feature. ", False )
    # scriptDialog.AddSelectionControlToGrid( "AudioBox", "FileBrowserControl", "", "All Files (*)", 4, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "SettingsLabel", "LabelControl", "Settings File (Optional)", 5, 0, "The Quicktime settings file to use. If not specified here, you will be prompted to specify your settings after pressing the Submit button.", False )
    scriptDialog.AddSelectionControlToGrid( "SettingsBox", "FileBrowserControl", "", "All Files (*)", 5, 1, colSpan=3 )
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Integration")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Project Management", 0, 0, colSpan=4 )
    
    scriptDialog.AddControlToGrid( "IntegrationLabel", "LabelControl", "Project Management", 1, 0, "", False )
    IntegrationTypeBox = scriptDialog.AddComboControlToGrid( "IntegrationTypeBox", "ComboControl", "Shotgun", IntegrationOptions, 1, 1, expand=False )
    IntegrationTypeBox.ValueModified.connect(IntegrationTypeBoxChanged)
    connectButton = scriptDialog.AddControlToGrid( "IntegrationConnectButton", "ButtonControl", "Connect...", 1, 2, expand=False )
    connectButton.ValueModified.connect(ConnectButtonPressed)
    createVersionBox = scriptDialog.AddSelectionControlToGrid( "CreateVersionBox", "CheckBoxControl", False, "Create new version", 1, 3, "If enabled, Deadline will connect to Shotgun/FTrack and create a new version for this job." )
    createVersionBox.ValueModified.connect(SubmitShotgunChanged)
    scriptDialog.SetEnabled( "CreateVersionBox", False )
    
    scriptDialog.AddControlToGrid( "IntegrationVersionLabel", "LabelControl", "Version", 2, 0, "The Shotgun/FTrack version name.", False )
    scriptDialog.AddControlToGrid( "IntegrationVersionBox", "TextControl", "", 2, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "IntegrationDescriptionLabel", "LabelControl", "Description", 3, 0, "The Shotgun/FTrack version description.", False )
    scriptDialog.AddControlToGrid( "IntegrationDescriptionBox", "TextControl", "", 3, 1, colSpan=3 )

    scriptDialog.AddControlToGrid( "IntegrationEntityInfoLabel", "LabelControl", "Selected Entity", 4, 0, "Information about the Shotgun/FTrack entity that the version will be created for.", False )
    entityInfoBox = scriptDialog.AddControlToGrid( "IntegrationEntityInfoBox", "MultiLineTextControl", "", 4, 1, colSpan=3 )
    entityInfoBox.ReadOnly = True
    
    scriptDialog.AddControlToGrid( "IntegrationDraftOptionsLabel", "LabelControl", "Draft Options", 5, 0, "Information about the Shotgun/FTrack entity that the version will be created for.", False )
    scriptDialog.AddSelectionControlToGrid( "IntegrationUploadMovieBox", "CheckBoxControl", False, "Create/Upload Movie", 5, 1, "If this option is enabled, a draft job will be created to upload a movie to shotgun." )
    scriptDialog.AddSelectionControlToGrid( "IntegrationUploadFilmStripBox", "CheckBoxControl", False, "Create/Upload Film Strip", 5, 2, "If this option is enabled, a draft job will be created to upload a filmstrip to shotgun." )
    scriptDialog.EndGrid()
    
    SubmitShotgunChanged( None )

    scriptDialog.EndTabPage()
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    settingsButton = scriptDialog.AddControlToGrid( "SettingsButton", "ButtonControl", "Create Settings", 0, 0, "Create a new Quicktime settings file. ", False )
    settingsButton.ValueModified.connect(SettingsButtonPressed)
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 1 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 2, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 3, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    settings = ("CategoryBox","PoolBox","GroupBox","PriorityBox","LimitGroupBox","OnJobCompleteBox","MachineListBox","SubmitSuspendedBox","IsBlacklistBox","FrameRateBox","CodecBox","SettingsBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    

    
    if len( args ) > 0:
        # scriptDialog.SetValue( "InputBox", args[0] )
        for i in range(len(fileSeqs)):
            inbox = "InputBox0" + str(i+1)
            # scriptDialog.SetValue( "InputBox", fileSeqs[i] )
            scriptDialog.SetValue( inbox, fileSeqs[i] )

    InputImagesModified()
    CodecChanged()
    
    LoadIntegrationSettings()
    updateDisplay()
    scriptDialog.SetValue("CreateVersionBox",False)
    
    startup = False
    
    if len( args ) > 7 and args[7] == "EnableShotgun":
        scriptDialog.SetEnabled( "CreateVersionBox", True )
        scriptDialog.SetValue( "CreateVersionBox", True )
    
    scriptDialog.ShowDialog( len( args ) > 0 )
    
def GetSettingsFilename():
    return Path.Combine(GetDeadlineSettingsPath(), "QuicktimeSettings.ini" )

def GetExtension():
    global scriptDialog
    
    codec = scriptDialog.GetValue( "CodecBox" )
    if codec == "3G":
        return ".3gp"
    elif codec == "AVI":
        return ".avi"
    elif codec == "DV Stream":
        return ".dv"
    elif codec == "FLC":
        return ".flc"
    elif codec == "MPEG-4":
        return ".mp4"
    elif codec == "QuickTime Movie":
        return ".mov"
    else:
        return ""

def fileSeqInfo(filename, num):
    initFrame = FrameUtils.GetFrameNumberFromFilename( filename )
    paddingSize = FrameUtils.GetPaddingSizeFromFilename( filename )
    
    startFrame = 0
    endFrame = 0
    outputPathFilename = ""
    
    #if initFrame >= 0 and paddingSize > 0:
    if paddingSize > 0:
        filename = FrameUtils.GetLowerFrameFilename( filename, initFrame, paddingSize )
        print "Filename: " + filename
        
        updatingOutputFile = True
        inboxNum = "InputBox0" + str(num)
        scriptDialog.SetValue( inboxNum, filename )
        updatingOutputFile = False
        
        startFrame = FrameUtils.GetLowerFrameRange( filename, initFrame, paddingSize )
        endFrame = FrameUtils.GetUpperFrameRange( filename, initFrame, paddingSize )
        
        if pluginName == "AfterEffects":
            outputPathFilename = fileDirectory + jobSceneName[:-3] + GetExtension()
            #outputPathFilename = Path.ChangeExtension( jobSceneName[:-3], GetExtension() )
        else:
            filenameWOPadding = FrameUtils.GetFilenameWithoutPadding( filename )
            print "Testing............." + filenameWOPadding
            tmp = filenameWOPadding.split('_.')
            print "Tmp 0: " + tmp[0]
            tmp2 = tmp[0].split('\\')
            print "Tmp 2: " + tmp2[-1]
            tmp3 = tmp2[-1].split('_')
            print "Tmp 3.1: " + tmp3[0]
            print "Tmp 3.2: " + tmp3[1]
            print "Project Phase: " + projectPhase
            print "Tmp 3.2: " + tmp3[2]                        
            tmp4 = tmp3[0] + "_" + tmp3[1] + "_" + projectPhase + "_" + tmp3[2]
            print "Tmp 4: " + tmp4    
            #print "New name: " + tmp4 + "." + tmp[1]
            filenameWOPadding = tmp4 + "." + tmp[1]
            #filenameWOPadding = tmp[0] + "." + tmp[1]
            
            #filenameWOPadding = filenameWOPadding.split('\\')[-1]
            print "File Name without padding: " + filenameWOPadding
            outputPathFilename = fileDirectory + filenameWOPadding
            print "File path: " + outputPathFilename
            
            outputPathFilename = Path.ChangeExtension( outputPathFilename, GetExtension() )
            #outputPathFilename = Path.ChangeExtension( FrameUtils.GetFilenameWithoutPadding( filename ), GetExtension() )
    else:
        outputPathFilename = Path.ChangeExtension( filename, GetExtension() )
            
    return (startFrame, endFrame, outputPathFilename)
    

def InputImagesModified(*args):
    global startup
    global updatingOutputFile
    
    if not updatingOutputFile:
        success = False
        fileExists = True
        jobNames = []
        
        try:            
            filename01 = scriptDialog.GetValue( "InputBox01" )
            filename02 = scriptDialog.GetValue( "InputBox02" )
            filename03 = scriptDialog.GetValue( "InputBox03" )
            filename04 = scriptDialog.GetValue( "InputBox04" )
            
            if filename01 != "":
                startFrame, endFrame, outputPathFilename = fileSeqInfo(filename01, 1)
                scriptDialog.SetValue( "StartFrameBox01", startFrame )
                scriptDialog.SetValue( "EndFrameBox01", endFrame )
                scriptDialog.SetValue( "OutputBox01", outputPathFilename )
                filename = Path.GetFileNameWithoutExtension(outputPathFilename.split("\\")[-1]) + "_" + userInitials
                print "File name 01______________" + filename
                jobNames.append(filename)
            else:
                fileExists = False

            if filename02 != "":
                startFrame, endFrame, outputPathFilename = fileSeqInfo(filename02, 2)
                scriptDialog.SetValue( "StartFrameBox02", startFrame )
                scriptDialog.SetValue( "EndFrameBox02", endFrame )
                scriptDialog.SetValue( "OutputBox02", outputPathFilename )
                filename = Path.GetFileNameWithoutExtension(outputPathFilename.split("\\")[-1]) + "_" + userInitials
                print "File name 02______________" + filename
                jobNames.append(filename)
            
            if filename03 != "":
                startFrame, endFrame, outputPathFilename = fileSeqInfo(filename03, 3)
                scriptDialog.SetValue( "StartFrameBox03", startFrame )
                scriptDialog.SetValue( "EndFrameBox03", endFrame )
                scriptDialog.SetValue( "OutputBox03", outputPathFilename )
                filename = Path.GetFileNameWithoutExtension(outputPathFilename.split("\\")[-1]) + "_" + userInitials
                print "File name 03______________" + filename
                jobNames.append(filename)
                
            if filename04 != "":
                startFrame, endFrame, outputPathFilename = fileSeqInfo(filename04, 4)
                scriptDialog.SetValue( "StartFrameBox04", startFrame )
                scriptDialog.SetValue( "EndFrameBox04", endFrame )
                scriptDialog.SetValue( "OutputBox04", outputPathFilename )
                filename = Path.GetFileNameWithoutExtension(outputPathFilename.split("\\")[-1]) + "_" + userInitials
                print "File name 04______________" + filename
                jobNames.append(filename)
            
            for i in jobNames:
                print "............................................." + i
            jobNamesString = ",".join( jobNames ) 
                
            if fileExists:
                #scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( outputPathFilename ) )
                if pluginName == "AfterEffects":
                    print "AE Plugin"
                    scriptDialog.SetValue( "NameBox", jobSceneName )
                else:
                    # scriptDialog.SetValue( "NameBox", Path.GetFileNameWithoutExtension( outputPathFilename ) + "_" + userInitials )#####
                    scriptDialog.SetValue( "NameBox", jobNamesString )#####

                if projectPhase != "":     
                    print "Project Phase: " + projectPhase
                    scriptDialog.SetValue( "ProjectPhaseBox", projectPhase )
                else:
                    fileInfo = filename.split("\\")
                    #TESTING#
                    print "TESTING"
                    print "File Info--------------- " + fileSeqs[0]
                    for i in fileInfo:
                        print i
                    print "TESTING"
                    #TESTING#
                    phase1 = fileInfo[7]
                    phase2 = phase1.split("_")
                    phase3 = phase2[-1]
                    print "Phase: " + phase3
                    scriptDialog.SetValue( "ProjectPhaseBox", phase3 )
                
                scriptDialog.SetValue( "FileTypeBox", GetExtension()[1:].upper() )
                scriptDialog.SetValue( "FrameSizeBox", frameSize )
#########################################################################################################
                
                success = True
            
        except Exception, e:
            if not startup:
                scriptDialog.ShowMessageBox( e.Message, "Error Parsing Input Images" )
        
        if not success:
            scriptDialog.SetValue( "InputBox01", "" )
            scriptDialog.SetValue( "StartFrameBox01", 0 )
            scriptDialog.SetValue( "EndFrameBox01", 0 )
            scriptDialog.SetValue( "OutputBox01", "" )
            scriptDialog.SetValue( "NameBox", "Untitled" )

def CodecChanged(*args):
    global scriptDialog
    
    outputPathFilename = scriptDialog.GetValue( "OutputBox01" )
    outputPathFilename = Path.ChangeExtension( outputPathFilename, GetExtension() )
    scriptDialog.SetValue( "OutputBox01", outputPathFilename )

def SettingsButtonPressed(*args):
    global scriptDialog
    
    codec = scriptDialog.GetValue( "CodecBox" )
    settingsFile = Path.Combine( ClientUtils.GetDeadlineTempPath(), "temp_quicktime_export_settings.xml" )
    
    qtGenerator = Path.Combine( ClientUtils.GetBinDirectory(), "deadlinequicktimegenerator" )
    process = ProcessUtils.SpawnProcess( qtGenerator, "-ExportSettings \"" + settingsFile + "\" \"" + codec + "\"", ClientUtils.GetBinDirectory() )
    
    ProcessUtils.WaitForExit( process, -1 )
    exitCode = process.ExitCode
    if exitCode != 0 and exitCode != 128:
        #scriptDialog.ShowMessageBox( "Export settings could not be generated. Either the process was canceled, the selected codec isn't supported, the version of QuickTime installed on this machine isn't supported, or an error occurred.", "Error Generating Export Settings" )
        return
    
    newSettingsFile = scriptDialog.ShowSaveFileBrowser( "quicktime_export_settings.xml", "All Files (*)" )
    if newSettingsFile != None:
        File.Copy( settingsFile, newSettingsFile, True )
        scriptDialog.SetValue( "SettingsBox", newSettingsFile )

def GetSupportedFormats():
    formats = ( ".3gp",
                ".3g2",
                ".aiff",
                ".aif",
                ".au",
                ".snd",
                ".avi",
                ".bmp",
                ".dv",
                ".swf",
                ".gif",
                ".jpg",
                ".pnt",
                ".mid",
                ".mp3",
                ".mpu",
                ".mpeg",
                ".mpg",
                ".mp4",
                ".m4a",
                ".pct",
                ".psd",
                ".png",
                ".qtz",
                ".qtif",
                ".qif",
                ".qti",
                ".sgi",
                ".smi",
                ".tga",
                ".tiff",
                ".tif",
                ".wav",
                ".wmv")
    return formats
    #formatFilename = Path.Combine( RepositoryUtils.GetRootDirectory(), "scripts/Submission/QuicktimeSubmission/SupportedFormats.ini" )
    #return File.ReadAllLines( formatFilename )

def IsFormatSupported( inputFile ):
    extension = Path.GetExtension( inputFile ).lower()
    supportedFormats = GetSupportedFormats()
    for format in supportedFormats:
        if extension == format.lower():
            return True
    return False


def ConnectButtonPressed( *args ):
    global scriptDialog
    script = ""
    settingsName = ""
    usingShotgun = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")
    
    if usingShotgun:
        script = Path.Combine( RepositoryUtils.GetRootDirectory(), "events/Shotgun/ShotgunUI.py" )
        settingsName = GetShotgunSettingsFilename()
    else:
        script = Path.Combine( RepositoryUtils.GetRootDirectory(), "submission/FTrack/Main/FTrackUI.py" )
        settingsName = GetFTrackSettingsFilename()
    output = ClientUtils.ExecuteCommandAndGetOutput( ("-ExecuteScript", script, "QuicktimeMonitor", "selectversion") )
    updated = ProcessLines( output.splitlines(), usingShotgun )
    if updated:
        File.WriteAllLines( settingsName, tuple(output.splitlines()) )
        updateDisplay()
    
def ProcessLines( lines, shotgun ):
    global shotgunSettings
    global fTrackSettings
    
    tempKVPs = {}
    
    for line in lines:
        line = line.strip()
        tokens = line.split( '=', 1 )
        
        if len( tokens ) > 1:
            key = tokens[0]
            value = tokens[1]
            tempKVPs[key] = value
    if len(tempKVPs)>0:
        if shotgun:
            shotgunSettings = tempKVPs
        else:
            fTrackSettings = tempKVPs
        return True
    return False
                           
def updateDisplay():
    global fTrackSettings
    global shotgunSettings
    
    displayText = ""
    if scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun":
        if 'UserName' in shotgunSettings:
            displayText += "User Name: %s\n" % shotgunSettings[ 'UserName' ]
        if 'TaskName' in shotgunSettings:
            displayText += "Task Name: %s\n" % shotgunSettings[ 'TaskName' ]
        if 'ProjectName' in shotgunSettings:
            displayText += "Project Name: %s\n" % shotgunSettings[ 'ProjectName' ]
        if 'EntityName' in shotgunSettings:
            displayText += "Entity Name: %s\n" % shotgunSettings[ 'EntityName' ]	
        if 'EntityType' in shotgunSettings:
            displayText += "Entity Type: %s\n" % shotgunSettings[ 'EntityType' ]
        if 'DraftTemplate' in shotgunSettings:
            displayText += "Draft Template: %s\n" % shotgunSettings[ 'DraftTemplate' ]
    
        scriptDialog.SetValue( "IntegrationEntityInfoBox", displayText )
        scriptDialog.SetValue( "IntegrationVersionBox", shotgunSettings.get( 'VersionName', "" ) )
        scriptDialog.SetValue( "IntegrationDescriptionBox", shotgunSettings.get( 'Description', "" ) )
    else:
        if 'FT_Username' in fTrackSettings:
            displayText += "User Name: %s\n" % fTrackSettings[ 'FT_Username' ]
        if 'FT_TaskName' in fTrackSettings:
            displayText += "Task Name: %s\n" % fTrackSettings[ 'FT_TaskName' ]
        if 'FT_ProjectName' in fTrackSettings:
            displayText += "Project Name: %s\n" % fTrackSettings[ 'FT_ProjectName' ]
    
        scriptDialog.SetValue( "IntegrationEntityInfoBox", displayText )
        scriptDialog.SetValue( "IntegrationVersionBox", fTrackSettings.get( 'FT_AssetName', "" ) )
        scriptDialog.SetValue( "IntegrationDescriptionBox", fTrackSettings.get( 'FT_Description', "" ) )
        
    if len(displayText)>0:
        scriptDialog.SetEnabled("CreateVersionBox",True)
        scriptDialog.SetValue("CreateVersionBox",True)
    else:
        scriptDialog.SetEnabled("CreateVersionBox",False)
        scriptDialog.SetValue("CreateVersionBox",False)

def LoadIntegrationSettings():
    global fTrackSettings
    global shotgunSettings
    fTrackSettings = {}
    shotgunSettings = {}
        
    settingsFile = GetShotgunSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), True )
        
    settingsFile = GetFTrackSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), False )

def IntegrationTypeBoxChanged():
    updateDisplay()
    
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun") and scriptDialog.GetValue( "CreateVersionBox" )
    scriptDialog.SetEnabled( "IntegrationUploadMovieBox", shotgunEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", shotgunEnabled )
    
def GetShotgunSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "QuicktimeMonitorSettingsShotgun.ini" )

def GetFTrackSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "QuicktimeMonitorSettingsFTrack.ini" )

def SubmitShotgunChanged( *args ):
    global scriptDialog
    
    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")
    
    scriptDialog.SetEnabled( "IntegrationVersionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationVersionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadMovieBox", integrationEnabled and shotgunEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", integrationEnabled and shotgunEnabled )
    
def CreateJob(inputFile, outputFile, i ):
    v = i+1
    jobInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_job_info_" + str(v) + ".job"  )
    jobNameString = scriptDialog.GetValue( "NameBox" )
    jobName = jobNameString.split(",")
    
    print "I AM WRITING OUT THIS:"
    print "Input File-------------------------------" + inputFile
    print "Output File-------------------------------" + outputFile
    print "Job Name-------------------------------" + jobName[i]
    codec = scriptDialog.GetValue( "CodecBox" )
    plugin = "Quicktime"
    settingsFile = scriptDialog.GetValue( "SettingsBox" ).strip()
    
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=%s" % plugin )
    writer.WriteLine( "Name=%s" % jobName[i] )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    # writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    
    writer.WriteLine( "ExtraInfo7=%s" % scriptDialog.GetValue( "ProjectPhaseBox" ) )
    writer.WriteLine( "ExtraInfo8=%s" % scriptDialog.GetValue( "FrameSizeBox" ) )
    writer.WriteLine( "ExtraInfo9=%s" % scriptDialog.GetValue( "FileTypeBox" ) )
    
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    # writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "MachineLimit=1" )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    startFrame = "StartFrameBox0" + str(i+1)
    endFrame = "EndFrameBox0" + str(i+1)
    writer.WriteLine( "Frames=%s-%s" % (scriptDialog.GetValue( startFrame ), scriptDialog.GetValue( endFrame )) )
    writer.WriteLine( "ChunkSize=100000" )
    writer.WriteLine( "OutputFilename0=%s" % outputFile )
    
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( ClientUtils.GetDeadlineTempPath(), "quicktime_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine( "InputImages=%s" % inputFile )
    writer.WriteLine( "OutputFile=%s" % outputFile )
    writer.WriteLine( "FrameRate=%s" % scriptDialog.GetValue( "FrameRateBox" ) )
    
    # Apple specific options
    writer.WriteLine( "Codec=%s" % codec )
    # writer.WriteLine( "AudioFile=%s" % audioFile )
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    arguments.Add( settingsFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
    


def SubmitButtonPressed(*args):
    global scriptDialog
    global shotgunSettings
        
############################################
    inputFiles = []
    inputFiles.append(scriptDialog.GetValue( "InputBox01" ).strip())
    inputFiles.append(scriptDialog.GetValue( "InputBox02" ).strip())
    inputFiles.append(scriptDialog.GetValue( "InputBox03" ).strip())
    inputFiles.append(scriptDialog.GetValue( "InputBox04" ).strip())
    
    if(len(inputFiles[0])==0):
        scriptDialog.ShowMessageBox("No input file specified","Error")
        return
        
    if( PathUtils.IsPathLocal( inputFiles[0] ) ):
        result = scriptDialog.ShowMessageBox( "The input file " + inputFiles[0] + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    if( not IsFormatSupported( inputFiles[0] ) ):
        # scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory(), "scripts/Submission/QuicktimeSubmission.py" )
        scriptPath = Path.Combine( RepositoryUtils.GetRootDirectory(), "custom/scripts/Submission/Quicktime/DEV_QuicktimeSubmission_02.py" )
        result = scriptDialog.ShowMessageBox( "The input file " + inputFiles[0] + " is not a supported format. If this format is supported by Quicktime, you can add its file extension to " + scriptPath + " to prevent this warning from appearing.\n\nDo you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    # Ensure the output file has the correct extension before the job is submitted.
    CodecChanged()
    
    outputFiles = []
    outputFiles.append(scriptDialog.GetValue( "OutputBox01" ).strip())
    outputFiles.append(scriptDialog.GetValue( "OutputBox02" ).strip())
    outputFiles.append(scriptDialog.GetValue( "OutputBox03" ).strip())
    outputFiles.append(scriptDialog.GetValue( "OutputBox04" ).strip())
    
    if(len(outputFiles[0])==0):
        scriptDialog.ShowMessageBox("No output file specified","Error")
        return
    if( not Directory.Exists( Path.GetDirectoryName( outputFiles[0] ) ) ):
        scriptDialog.ShowMessageBox( "Path for the output file " + outputFiles[0] + " does not exist.", "Error" )
        return
    elif( PathUtils.IsPathLocal( outputFiles[0] ) ):
        result = scriptDialog.ShowMessageBox( "The output file " + outputFiles[0] + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return 
        
    jobName = scriptDialog.GetValue( "NameBox" )
    print "############################# Job Name ################################"
    print jobName
    print "############################# Job Name ################################"
    
    for i in range(len(outputFiles)):
        print "hi"        
        if outputFiles[i]:
            print "I AM SENDING TO:"
            print "Index number: " + str(i)
            print "Input.................................." + inputFiles[i]
            print "Output................................." + outputFiles[i]
            CreateJob(inputFiles[i], outputFiles[i], i)
    
########################################################
########################################################
    

    
        