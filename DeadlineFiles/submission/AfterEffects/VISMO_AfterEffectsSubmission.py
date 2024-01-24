from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.IO import File

from Deadline.Scripting import *

import re, sys, os, mimetypes, traceback, glob

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
shotgunSettings = {}
fTrackSettings = {}
IntegrationOptions = ["Shotgun","FTrack"]
########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    
    dialogWidth = 600
    dialogHeight = 682
    labelWidth = 120
    controlWidth = 152
    
    tabWidth = dialogWidth - 16
    tabHeight = 630
    
    scriptDialog = DeadlineScriptDialog()

    #scriptDialog.SetSize(dialogWidth+16,dialogHeight)
    scriptDialog.SetTitle("Submit After Effects Job To Deadline")
    scriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/AfterEffects/AfterEffects.ico" ) )

    scriptDialog.AddTabControl("Job Options Tabs", dialogWidth+8, tabHeight)
    
    scriptDialog.AddTabPage("Job Options")
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 0, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 0, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 1, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 2, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 2, 1 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator2", "SeparatorControl", "Job Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "PoolLabel", "LabelControl", "Pool", 0, 0, "The pool that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "PoolBox", "PoolComboControl", "none", 0, 1 )

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 1, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 1, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 2, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 2, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 3, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 4, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 5, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 6, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 7, 0, "The whitelisted or blacklisted list of machines.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 7, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limit Groups", 8, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 9, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 10, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 10, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "After Effects Options", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "After Effects File", 0, 0, "The project file to render.", False )
    scriptDialog.AddSelectionControlToGrid( "SceneBox", "FileBrowserControl", "", "After Effects Files (*.aep *.aepx)", 0, 1, colSpan=2 )

    scriptDialog.AddControlToGrid("CompLabel", "LabelControl", "Composition", 1, 0, "The composition in the project file to render. If left blank, the entire render queue will be rendered as a single task.", False)
    
    compBox = scriptDialog.AddControlToGrid("CompBox", "TextControl", "", 1, 1, colSpan=2 )
    compBox.ValueModified.connect(CompChanged)
    
    scriptDialog.AddControlToGrid("OutputLabel","LabelControl","Output (optional)", 2, 0, "Override the output path for the composition. This is optional, and can be left blank.", False)
    scriptDialog.AddSelectionControlToGrid("OutputBox","FileSaverControl","", "All Files (*)",2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 3, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 4, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 4, 1 )
    scriptDialog.AddSelectionControlToGrid( "MultiProcess", "CheckBoxControl", False, "Use Multi-Process Rendering", 4, 2, "Enable to use multiple processes to render multiple frames simultaneously." )

    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 5, 0 , "The version of After Effects to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "CS6", ("CS3","CS4","CS5","CS5.5","CS6", "CC", "CC2014"), 5, 1 )
    versionBox.ValueModified.connect(VersionChanged)

    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Project File", 5, 2, "If this option is enabled, the project file you want to render will be submitted with the job, and then copied locally to the slave machine during rendering." )
    scriptDialog.EndGrid()
    
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage( "Advanced Options" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator9", "SeparatorControl", "Multi-Machine Rendering", 0, 0, colSpan=4 )
    scriptDialog.AddControlToGrid( "MultiMachineLabel", "LabelControl", "Note that \"Skip existing frames\" must be enabled for each comp", 1, 0, colSpan=3)
    
    multiMachineCheckBox = scriptDialog.AddSelectionControlToGrid("MultiMachineBox", "CheckBoxControl", False, "Enable Multi-Machine Rendering", 2, 0, "This mode submits a special job where each task represents the full frame range. The slaves will all work on the same frame range, but because 'Skip existing frames' is enabled for the comps, they will skip frames that other slaves are already rendering.")
    multiMachineCheckBox.ValueModified.connect(MultiMachineChanged)

    scriptDialog.AddControlToGrid( "MultiMachineTasksLabel", "LabelControl", "Number Of Tasks", 3, 0, "The number of tasks actually represents the number of slaves that can work on this job at the same time. Each slave gets a task, which represents the full frame range, and they will work together until all frames are complete.", False )
    scriptDialog.AddRangeControlToGrid("MultiMachineTasksBox", "RangeControl", 10, 1, 9999, 0, 1, 3, 1 )
    
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Memory Management Options", 4, 0, colSpan=4 )

    memManageCheckBox = scriptDialog.AddSelectionControlToGrid("MemoryManagement", "CheckBoxControl", False, "Enable Memory Mangement", 5, 0, "Whether or not to use the memory management options. ", colSpan=3)
    memManageCheckBox.ValueModified.connect(MemoryManageChanged)


    scriptDialog.AddControlToGrid( "ImageCacheLabel", "LabelControl", "Image Cache %", 6, 0, "The maximum amount of memory after effects will use to cache frames. ", False )
    scriptDialog.AddRangeControlToGrid("ImageCachePercentage", "RangeControl", 100, 20, 100, 0, 1, 6, 1 )

    scriptDialog.AddControlToGrid( "MaxMemoryLabel", "LabelControl", "Max Memory %", 7, 0, "The maximum amount of memory After Effects can use overall. ", False )
    scriptDialog.AddRangeControlToGrid("MaxMemoryPercentage", "RangeControl", 100, 20, 100, 0, 1, 7, 1)
    
    scriptDialog.AddControlToGrid( "Separator6", "SeparatorControl", "Miscellaneous Options", 8, 0, colSpan=4 )
    scriptDialog.AddSelectionControlToGrid( "MissingLayers", "CheckBoxControl", False, "Ignore Missing Layer Dependencies", 9, 0, "If enabled, Deadline will ignore errors due to missing layer dependencies. ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "MissingEffects", "CheckBoxControl", False, "Ignore Missing Effect References", 10, 0, "If enabled, Deadline will ignore errors due to missing effect references. ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "MissingFootage", "CheckBoxControl", False, "Continue On Missing Footage", 11, 0, "If enabled, rendering will not stop when missing footage is detected (After Effects CS4 and later). ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "FailOnWarnings", "CheckBoxControl", False, "Fail On Warning Messages", 12, 0, "If enabled, Deadline will fail the job whenever After Effects prints out a warning message. ", colSpan=3)
    scriptDialog.AddSelectionControlToGrid( "LocalRendering", "CheckBoxControl", False, "Enable Local Rendering", 13, 0, "If enabled, the frames will be rendered locally, and then copied to their final network location. This requires the Output to be overwritten.", colSpan=3)

    overrideButton = scriptDialog.AddSelectionControlToGrid( "OverrideFailOnExistingAEProcess", "CheckBoxControl", False, "Override Fail On Existing AE Process", 14, 0, "If enabled, the Fail On Existing AE Process Setting will be taken into account.", colSpan=2)
    overrideButton.ValueModified.connect(OverrideButtonPressed)
    scriptDialog.AddSelectionControlToGrid( "FailOnExistingAEProcess", "CheckBoxControl", False, "Fail On Existing AE Process", 14, 2, "If enabled, Deadline will fail the job whilst any After Effects instance is running.")

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
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator8", "SeparatorControl", "Draft", 0, 0 )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()

    draftSubmitButton = scriptDialog.AddSelectionControlToGrid( "DraftSubmitBox", "CheckBoxControl", False, "Submit Draft Job On Completion", 0, 1, "If enabled, Deadline will automatically submit a Draft job after this job completes." )
    draftSubmitButton.ValueModified.connect(SubmitDraftChanged)

    scriptDialog.AddSelectionControlToGrid( "DraftUploadShotgunBox", "CheckBoxControl", False, "Upload Draft Results To Shotgun", 0, 2, "If enabled, the Draft results will be uploaded to Shotgun when it is complete." )
    scriptDialog.SetEnabled( "DraftUploadShotgunBox", False )

    scriptDialog.AddControlToGrid( "DraftTemplateLabel", "LabelControl", "Draft Template", 1, 0, "The Draft template file to use.", False )
    scriptDialog.AddSelectionControlToGrid( "DraftTemplateBox", "FileBrowserControl", "", "Template Files (*.py);;All Files (*)", 1, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DraftUserLabel", "LabelControl", "User Name", 2, 0, "The user name used by the Draft template.", False )
    scriptDialog.AddControlToGrid( "DraftUserBox", "TextControl", "", 2, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DraftEntityLabel", "LabelControl", "Entity Name", 3, 0, "The entity name used by the Draft template.", False )
    scriptDialog.AddControlToGrid( "DraftEntityBox", "TextControl", "", 3, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DraftVersionLabel", "LabelControl", "Version Name", 4, 0, "The version name used by the Draft template.", False )
    scriptDialog.AddControlToGrid( "DraftVersionBox", "TextControl", "", 4, 1, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "ArgsLabel", "LabelControl", "Additional Args", 5, 0, "The arguments to pass to the script. If no extra arguments are required, leave this blank.", False )
    scriptDialog.AddControlToGrid( "ArgsBox", "TextControl", "", 5, 1, colSpan=2 )

    draftShotgunButton = scriptDialog.AddControlToGrid( "DraftShotgunButton", "ButtonControl", "Use Shotgun Data", 6, 1, expand=False)
    draftShotgunButton.ValueModified.connect(DraftShotgunButtonPressed)

    scriptDialog.EndGrid()
    
    SubmitShotgunChanged( None )
    SubmitDraftChanged( None )
    scriptDialog.EndTabPage()
    
    scriptDialog.EndTabControl()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
    #might need to add some settings here for the memory management options
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","SceneBox","FramesBox","ChunkSizeBox","VersionBox","ArgsBox","MemoryManagement","ImageCachePercentage", "MaxMemoryPercentage", "CompBox", "MultiProcess", "SubmitSceneBox", "OutputBox", "MissingLayers", "MissingEffects", "MissingFootage", "FailOnWarnings", "LocalRendering", "OverrideFailOnExistingAEProcess", "FailOnExistingAEProcess", "DraftTemplateBox", "DraftUserBox", "DraftEntityBox", "DraftVersionBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )

    LoadIntegrationSettings()
    updateDisplay()
    scriptDialog.SetValue("CreateVersionBox",False)
    
    CompChanged(None)
    VersionChanged(None)
    MultiMachineChanged(None)
    OverrideButtonPressed(None)
    MemoryManageChanged(None)
    
    #check if memory management is enabled
    if(not bool(scriptDialog.GetValue("MemoryManagement"))):
        scriptDialog.SetEnabled("ImageCachePercentage", False)
        scriptDialog.SetEnabled("MaxMemoryPercentage", False)
    
    scriptDialog.ShowDialog(False)
    
def GetVersionNumber():
    global scriptDialog
    
    versionStr = scriptDialog.GetValue( "VersionBox" )
    if versionStr == "CC":
        return 12.0
    elif versionStr.startswith( "CC" ):
        year = int(versionStr[2:])
        return float(year - 2001)
    elif versionStr.startswith( "CS" ):
        return (float(versionStr.replace("CS","")) + 5)
    else:
        return float(versionStr)

def IsMovieFormat( extension ):
    cleanExtension = extension.lstrip( '.' )
    if len( cleanExtension ) > 0:
        cleanExtension = cleanExtension.lower()
        # These formats are all the ones included in DFusion, as well
        # as all the formats in AE that don't contain [#####].
        if cleanExtension == "vdr" or cleanExtension == "wav" or cleanExtension == "dvs" or cleanExtension == "fb"  or cleanExtension == "omf" or cleanExtension == "omfi"or cleanExtension == "stm" or cleanExtension == "tar" or cleanExtension == "vpr" or cleanExtension == "gif" or cleanExtension == "img" or cleanExtension == "flc" or cleanExtension == "flm" or cleanExtension == "mp3" or cleanExtension == "mov" or cleanExtension == "rm"  or cleanExtension == "avi" or cleanExtension == "wmv" or cleanExtension == "mpg" or cleanExtension == "m4a" or cleanExtension == "mpeg":
            return True
    return False

def CompChanged(*args):
    global scriptDialog
    
    enabled = (scriptDialog.GetValue( "CompBox" ) != "" and not scriptDialog.GetValue( "MultiMachineBox" ))
    scriptDialog.SetEnabled( "OutputLabel", enabled )
    scriptDialog.SetEnabled( "OutputBox", enabled )
    scriptDialog.SetEnabled( "FramesLabel", enabled )
    scriptDialog.SetEnabled( "FramesBox", enabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", enabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", enabled )
    
def VersionChanged(*args):
    global scriptDialog
    
    version = GetVersionNumber()
    scriptDialog.SetEnabled( "MissingFootage", (version > 8 ) )
    
def MultiMachineChanged(*args):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "MultiMachineBox" ) 
    scriptDialog.SetEnabled( "MultiMachineTasksBox" ,enabled )
    
    framesEnabled = not enabled and (scriptDialog.GetValue( "CompBox" ) != "")
    scriptDialog.SetEnabled( "OutputLabel", framesEnabled )
    scriptDialog.SetEnabled( "OutputBox", framesEnabled )
    scriptDialog.SetEnabled( "FramesLabel", framesEnabled )
    scriptDialog.SetEnabled( "FramesBox", framesEnabled )
    scriptDialog.SetEnabled( "ChunkSizeLabel", framesEnabled )
    scriptDialog.SetEnabled( "ChunkSizeBox", framesEnabled )

def OverrideButtonPressed(*args):
    global scriptDialog

    enabled = scriptDialog.GetValue( "OverrideFailOnExistingAEProcess" )

    scriptDialog.SetEnabled( "FailOnExistingAEProcess" ,enabled )
    
def MemoryManageChanged(*args):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "MemoryManagement" ) 
    
    scriptDialog.SetEnabled( "ImageCacheLabel" ,enabled )
    scriptDialog.SetEnabled( "ImageCachePercentage" ,enabled )
    scriptDialog.SetEnabled( "MaxMemoryLabel" , enabled )
    scriptDialog.SetEnabled( "MaxMemoryPercentage" , enabled )
    
def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "AfterEffectsSettings.ini" )
    
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
    output = ClientUtils.ExecuteCommandAndGetOutput( ("-ExecuteScript", script, "AfterEffectsMonitor") )
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
        SubmitDraftChanged(None)
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
    return Path.Combine( GetDeadlineSettingsPath(), "AfterEffectsMonitorSettingsShotgun.ini" )

def GetFTrackSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "AfterEffectsMonitorSettingsFTrack.ini" )

def SubmitShotgunChanged( *args ):
    global scriptDialog
    
    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    draftEnabled = scriptDialog.GetValue( "DraftSubmitBox" )
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")
    
    scriptDialog.SetEnabled( "IntegrationVersionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationVersionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadMovieBox", integrationEnabled and shotgunEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", integrationEnabled and shotgunEnabled )
    
    scriptDialog.SetEnabled( "DraftUploadShotgunBox", integrationEnabled and draftEnabled and shotgunEnabled )
    scriptDialog.SetEnabled( "DraftShotgunButton", integrationEnabled and draftEnabled and shotgunEnabled )

def DraftShotgunButtonPressed( *args ):
    global scriptDialog
    global shotgunSettings
        
    user = shotgunSettings.get( 'UserName', "" )
    task = shotgunSettings.get( 'TaskName', "" )
    project = shotgunSettings.get( 'ProjectName', "" )
    entity = shotgunSettings.get( 'EntityName', "" )
    draftTemplate = shotgunSettings.get( 'DraftTemplate', "" )
    
    entityName = ""
    if task.strip() != "" and task.strip() != "None":
        entityName = task
    elif project.strip() != "" and entity.strip() != "":
        entityName = "%s > %s" % (project, entity)
    
    draftTemplateName = ""
    if draftTemplate.strip() != "" and draftTemplate != "None":
        draftTemplateName = draftTemplate
    
    version = scriptDialog.GetValue( "IntegrationVersionBox" )
    
    scriptDialog.SetValue( "DraftTemplateBox", draftTemplateName )
    scriptDialog.SetValue( "DraftUserBox", user )
    scriptDialog.SetValue( "DraftEntityBox", entityName )
    scriptDialog.SetValue( "DraftVersionBox", version )
    
def SubmitDraftChanged( *args ):
    global scriptDialog
    
    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    draftEnabled = scriptDialog.GetValue( "DraftSubmitBox" )
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")
    
    scriptDialog.SetEnabled( "DraftTemplateLabel", draftEnabled )
    scriptDialog.SetEnabled( "DraftTemplateBox", draftEnabled )
    scriptDialog.SetEnabled( "DraftUserLabel", draftEnabled )
    scriptDialog.SetEnabled( "DraftUserBox", draftEnabled )
    scriptDialog.SetEnabled( "DraftEntityLabel", draftEnabled )
    scriptDialog.SetEnabled( "DraftEntityBox", draftEnabled )
    scriptDialog.SetEnabled( "DraftVersionLabel", draftEnabled )
    scriptDialog.SetEnabled( "DraftVersionBox", draftEnabled )
    scriptDialog.SetEnabled( "ArgsLabel", draftEnabled )
    scriptDialog.SetEnabled( "ArgsBox", draftEnabled )
    
    scriptDialog.SetEnabled( "DraftUploadShotgunBox", shotgunEnabled and integrationEnabled and draftEnabled )
    scriptDialog.SetEnabled( "DraftShotgunButton", shotgunEnabled and integrationEnabled and draftEnabled )
    
    
def SubmitButtonPressed(*args):
    global scriptDialog
    global shotgunSettings
    
    if scriptDialog.GetValue( "DraftSubmitBox" ):
        if scriptDialog.GetValue("CompBox") == "" or scriptDialog.GetValue( "OutputBox" ).strip() == "":
            scriptDialog.ShowMessageBox( "A Draft job can only be submitted if you specify a Composition name and the Output File under the After Effects Options.", "Error" )
            return
        
        draftTemplate = scriptDialog.GetValue( "DraftTemplateBox" )		
        if( not File.Exists( draftTemplate ) ):
            scriptDialog.ShowMessageBox( "Draft template file \"%s\" does not exist" % draftTemplate, "Error" )
            return
        elif( PathUtils.IsPathLocal( draftTemplate ) ):
            result = scriptDialog.ShowMessageBox( "The Draft template file \"%s\" is local, are you sure you want to continue?" % draftTemplate,"Warning", ("Yes","No") )
            if( result == "No" ):
                return
    
    submitScene = bool(scriptDialog.GetValue("SubmitSceneBox"))
    multiMachine = bool(scriptDialog.GetValue("MultiMachineBox"))
    
    # Check if scene file exists
    sceneFile = scriptDialog.GetValue( "SceneBox" )
    if( not File.Exists( sceneFile ) ):
        scriptDialog.ShowMessageBox("Project file %s does not exist." % sceneFile, "Error" )
        return
    elif(not submitScene and PathUtils.IsPathLocal(sceneFile)):
        result = scriptDialog.ShowMessageBox("The project file " + sceneFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
        if( result == "No" ):
            return
    
    outputFile = ""
    frames = ""
    jobName = scriptDialog.GetValue( "NameBox" )
    jobName = jobName[:-4]
    
    # Get the comp
    comp = scriptDialog.GetValue("CompBox")
    if comp != "":
        # Check that the output is valid
        outputFile = scriptDialog.GetValue( "OutputBox" ).strip()
        if len(outputFile) > 0:
            if not Directory.Exists( Path.GetDirectoryName(outputFile) ):
                scriptDialog.ShowMessageBox( "The directory of the output file does not exist:\n" + Path.GetDirectoryName(outputFile), "Error" )
                return
            elif(PathUtils.IsPathLocal(outputFile)):
                result = scriptDialog.ShowMessageBox("The output file " + outputFile + " is local, are you sure you want to continue?","Warning", ("Yes","No") )
                if( result == "No" ):
                    return
            
            extension = Path.GetExtension( outputFile )
            if not IsMovieFormat( extension ):
                if outputFile.find( "[#" ) < 0 and outputFile.find( "#]" ) < 0:
                    directory = Path.GetDirectoryName( outputFile )
                    filename = Path.GetFileNameWithoutExtension( outputFile )
                    outputFile = Path.Combine( directory, filename + "[#####]" + extension )
        
        #Since we don't specify ranges for multi-machine rendering, don't check frame range when Multi-Machine Rendering = True
        if not multiMachine:
            # Check if a valid frame range has been specified.
            frames = scriptDialog.GetValue( "FramesBox" )
            if( not FrameUtils.FrameRangeValid( frames ) ):
                scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
                return
    else:
        jobName = jobName + " - Entire Render Queue"
    
    if multiMachine:
        jobName = jobName + " (multi-machine rendering)"
    
    # Create job info file.
    jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "ae_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=AfterEffects" )
    writer.WriteLine( "Name=%s" % jobName )
    writer.WriteLine( "Comment=%s" % scriptDialog.GetValue( "CommentBox" ) )
    writer.WriteLine( "Department=%s" % scriptDialog.GetValue( "DepartmentBox" ) )
    writer.WriteLine( "Pool=%s" % scriptDialog.GetValue( "PoolBox" ) )
    writer.WriteLine( "SecondaryPool=%s" % scriptDialog.GetValue( "SecondaryPoolBox" ) )
    writer.WriteLine( "Group=%s" % scriptDialog.GetValue( "GroupBox" ) )
    writer.WriteLine( "Priority=%s" % scriptDialog.GetValue( "PriorityBox" ) )
    writer.WriteLine( "TaskTimeoutMinutes=%s" % scriptDialog.GetValue( "TaskTimeoutBox" ) )
    writer.WriteLine( "EnableAutoTimeout=%s" % scriptDialog.GetValue( "AutoTimeoutBox" ) )
    writer.WriteLine( "ConcurrentTasks=%s" % scriptDialog.GetValue( "ConcurrentTasksBox" ) )
    writer.WriteLine( "LimitConcurrentTasksToNumberOfCpus=%s" % scriptDialog.GetValue( "LimitConcurrentTasksBox" ) )
    
    if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
        writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    else:
        writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
    
    writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
    writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
    writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
    
    if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
        writer.WriteLine( "InitialStatus=Suspended" )
    
    if multiMachine:
        writer.WriteLine( "MachineLimit=0" )
        writer.WriteLine( "Frames=1-%s" % scriptDialog.GetValue( "MultiMachineTasksBox" ) )
        writer.WriteLine( "ChunkSize=1" )
    else:
        if comp != "":
            writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
            writer.WriteLine( "Frames=%s" % frames )
            writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
        else:
            writer.WriteLine( "MachineLimit=1" )
            writer.WriteLine( "Frames=0" )
            writer.WriteLine( "ChunkSize=1" )
    
    if len(outputFile) > 0:
        writer.WriteLine( "OutputFilename0=%s" % outputFile.replace( "[#####]", "#####" ) )
    
    #Shotgun/Draft
    extraKVPIndex = 0
    groupBatch = False
    if scriptDialog.GetValue( "CreateVersionBox" ):
        if scriptDialog.GetValue( "IntegrationTypeBox" ) == "Shotgun":
            writer.WriteLine( "ExtraInfo0=%s\n" % shotgunSettings.get('TaskName', "") )
            writer.WriteLine( "ExtraInfo1=%s\n" % shotgunSettings.get('ProjectName', "") )
            writer.WriteLine( "ExtraInfo2=%s\n" % shotgunSettings.get('EntityName', "") )
            writer.WriteLine( "ExtraInfo3=%s\n" % scriptDialog.GetValue( "IntegrationVersionBox" ) )
            writer.WriteLine( "ExtraInfo4=%s\n" % scriptDialog.GetValue( "IntegrationDescriptionBox" ) )
            writer.WriteLine( "ExtraInfo5=%s\n" % shotgunSettings.get('UserName', "") )
            
            for key in shotgunSettings:
                if key != 'DraftTemplate':
                    writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, shotgunSettings[key]) )
                    extraKVPIndex += 1
            if scriptDialog.GetValue("IntegrationUploadMovieBox"):
                writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateSGMovie=True\n" % (extraKVPIndex) )
                extraKVPIndex += 1
                groupBatch = True
            if scriptDialog.GetValue("IntegrationUploadFilmStripBox"):
                writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateSGFilmstrip=True\n" % (extraKVPIndex) )
                extraKVPIndex += 1
                groupBatch = True
        else:
            writer.WriteLine( "ExtraInfo0=%s\n" % fTrackSettings.get('FT_TaskName', "") )
            writer.WriteLine( "ExtraInfo1=%s\n" % fTrackSettings.get('FT_ProjectName', "") )
            writer.WriteLine( "ExtraInfo2=%s\n" % scriptDialog.GetValue( "IntegrationVersionBox" ) )
            writer.WriteLine( "ExtraInfo4=%s\n" % scriptDialog.GetValue( "IntegrationDescriptionBox" ) )
            writer.WriteLine( "ExtraInfo5=%s\n" % fTrackSettings.get('FT_Username', "") )
            for key in fTrackSettings:
                writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, fTrackSettings[key]) )
                extraKVPIndex += 1
    if scriptDialog.GetValue( "DraftSubmitBox" ):
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftTemplate=%s\n" % (extraKVPIndex, scriptDialog.GetValue( "DraftTemplateBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftUsername=%s\n" % (extraKVPIndex, scriptDialog.GetValue( "DraftUserBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftEntity=%s\n" % (extraKVPIndex, scriptDialog.GetValue( "DraftEntityBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftVersion=%s\n" % (extraKVPIndex, scriptDialog.GetValue( "DraftVersionBox" ) ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftUploadToShotgun=%s\n" % (extraKVPIndex, scriptDialog.GetValue( "DraftUploadShotgunBox" ) and scriptDialog.GetValue( "CreateVersionBox" ) and (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun") ) )
        extraKVPIndex += 1
        writer.WriteLine( "ExtraInfoKeyValue%d=DraftExtraArgs=%s\n" % (extraKVPIndex, scriptDialog.GetValue( "ArgsBox" ) ) )
        extraKVPIndex += 1
    if groupBatch:
        writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
    writer.Close()
    # Create plugin info file.
    version = GetVersionNumber()
    
    pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "ae_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    if(not bool(scriptDialog.GetValue("SubmitSceneBox"))):
        writer.WriteLine("SceneFile=%s" % scriptDialog.GetValue("SceneBox").replace("\\","/").strip())
        
    writer.WriteLine("Comp=%s" % scriptDialog.GetValue("CompBox"))
    writer.WriteLine("Version=%s" % str(version) )
    writer.WriteLine("IgnoreMissingLayerDependenciesErrors=%s" % scriptDialog.GetValue("MissingLayers"))
    writer.WriteLine("IgnoreMissingEffectReferencesErrors=%s" % scriptDialog.GetValue("MissingEffects"))
    writer.WriteLine("FailOnWarnings=%s" % scriptDialog.GetValue("FailOnWarnings"))
    
    if multiMachine:
        writer.WriteLine("MultiMachineMode=True")
    else:
        writer.WriteLine("LocalRendering=%s" % scriptDialog.GetValue("LocalRendering"))
    
    writer.WriteLine("OverrideFailOnExistingAEProcess=%s" % scriptDialog.GetValue("OverrideFailOnExistingAEProcess"))
    writer.WriteLine("FailOnExistingAEProcess=%s" % scriptDialog.GetValue("OverrideFailOnExistingAEProcess"))

    writer.WriteLine("MemoryManagement=%s" % scriptDialog.GetValue("MemoryManagement"))
    writer.WriteLine("ImageCachePercentage=%s" % scriptDialog.GetValue("ImageCachePercentage"))
    writer.WriteLine("MaxMemoryPercentage=%s" % scriptDialog.GetValue("MaxMemoryPercentage"))
    
    writer.WriteLine("MultiProcess=%s" % scriptDialog.GetValue("MultiProcess"))
    if version > 8:
        writer.WriteLine("ContinueOnMissingFootage=%s" % scriptDialog.GetValue("MissingFootage"))
       
    
    if len(outputFile) > 0:
        writer.WriteLine("Output=%s" % outputFile)
    
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    if scriptDialog.GetValue( "SubmitSceneBox" ):
        arguments.Add( sceneFile )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
