import traceback
import os
import re

from System import *
from System.Collections.Specialized import *
from System.IO import *
from System.Text import *

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


########################################################################
## Globals
########################################################################
scriptDialog = None
outputBox = None
sceneBox = None
defaultLocation = None
settings = None
shotgunSettings = {}
fTrackSettings = {}
nimSettings = {}
IntegrationOptions = ["Shotgun","FTrack", "NIM"]

print ("Hello 01")

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__( *args ):
    print ("Hello 02")
    global scriptDialog
    global settings
    global defaultLocation
    global outputBox
    global sceneBox

    defaultLocation = ""
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Maya Job To Deadline" )
    scriptDialog.SetIcon( scriptDialog.GetIcon( 'MayaBatch' ) )
    
    scriptDialog.AddTabControl("Tabs", 0, 0)
    
    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2 )
    
    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )    
    
###################################################
    scriptDialog.AddControlToGrid( "ProjectCodeLabel", "LabelControl", "Project Code", 4, 0, "The Project you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "ProjectCodeBox", "TextControl", "", 4, 1 )
    
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

    scriptDialog.AddControlToGrid( "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 2, 0, "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves.", False )
    scriptDialog.AddControlToGrid( "SecondaryPoolBox", "SecondaryPoolComboControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "GroupLabel", "LabelControl", "Group", 3, 0, "The group that your job will be submitted to.", False )
    scriptDialog.AddControlToGrid( "GroupBox", "GroupComboControl", "none", 3, 1 )

    scriptDialog.AddControlToGrid( "PriorityLabel", "LabelControl", "Priority", 4, 0, "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.", False )
    scriptDialog.AddRangeControlToGrid( "PriorityBox", "RangeControl", RepositoryUtils.GetMaximumPriority() / 2, 0, RepositoryUtils.GetMaximumPriority(), 0, 1, 4, 1 )

    scriptDialog.AddControlToGrid( "TaskTimeoutLabel", "LabelControl", "Task Timeout", 5, 0, "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "TaskTimeoutBox", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1 )
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "" )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddControlToGrid( "MachineListBox", "MachineListControl", "", 8, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "LimitGroupLabel", "LabelControl", "Limits", 9, 0, "The Limits that your job requires.", False )
    scriptDialog.AddControlToGrid( "LimitGroupBox", "LimitGroupControl", "", 9, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "DependencyLabel", "LabelControl", "Dependencies", 10, 0, "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.", False )
    scriptDialog.AddControlToGrid( "DependencyBox", "DependencyControl", "", 10, 1, colSpan=2 )

    scriptDialog.AddControlToGrid( "OnJobCompleteLabel", "LabelControl", "On Job Complete", 11, 0, "If desired, you can automatically archive or delete the job when it completes.", False )
    scriptDialog.AddControlToGrid( "OnJobCompleteBox", "OnJobCompleteControl", "Nothing", 11, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSuspendedBox", "CheckBoxControl", False, "Submit Job As Suspended", 11, 2, "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Maya Options", 0, 0, colSpan=4 )
    
    ###################################################
    scriptDialog.AddControlToGrid( "FramesLabel", "LabelControl", "Frame List", 1, 0, "The list of frames to render.", False )
    scriptDialog.AddControlToGrid( "FramesBox", "TextControl", "", 1, 1 )
    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Frames Per Task", 2, 0, "This is the number of frames that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 1 )
    scriptDialog.AddControlToGrid( "CameraLabel", "LabelControl", "Camera (optional)", 3, 0, "Leave blank to render using the default camera settings.", False )
    scriptDialog.AddComboControlToGrid( "CameraBox", "ComboControl", "", ("none",), 3, 1, colSpan=1 )  
    ###################################################

    scriptDialog.AddControlToGrid("ProjectLabel","LabelControl","Project Path", 4, 0, "The Maya project folder (this should be a shared folder on the network).", False)
    projBox = scriptDialog.AddSelectionControlToGrid("ProjectBox","FolderBrowserControl","","", 4, 1, colSpan=3)
    projBox.ValueModified.connect(SetDefaultLocation)
    defaultLocation = scriptDialog.GetValue( "ProjectBox" );

    scriptDialog.AddControlToGrid( "SceneLabel", "LabelControl", "Maya File", 5, 0, "The scene file to be rendered.", False )
    sceneBox = scriptDialog.AddSelectionControlToGrid( "SceneBox", "MultiFileBrowserControl", "", "Maya Files (*.ma *.mb)",5, 1, colSpan=3, browserLocation=defaultLocation )

    scriptDialog.AddControlToGrid("OutputLabel","LabelControl","Output Path",6, 0, "The folder where your output will be dumped (this should be a shared folder on the network).", False)
    outputBox = scriptDialog.AddSelectionControlToGrid("OutputBox","FolderBrowserControl", "","", 6, 1, colSpan=3, browserLocation=defaultLocation)
    
    ###################################################
    scriptDialog.AddControlToGrid( "BuildLabel", "LabelControl", "Build To Force", 7, 0, "You can force 32 or 64 bit rendering with this option.", False )
    scriptDialog.AddComboControlToGrid( "BuildBox", "ComboControl", "None", ("None","32bit","64bit"), 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "SubmitSceneBox", "CheckBoxControl", False, "Submit Maya Scene File", 7, 2, "If this option is enabled, the scene file will be submitted with the job, and then copied locally to the slave machine during rendering.", colSpan=2 )
    mayaBatchBox = scriptDialog.AddSelectionControlToGrid( "MayaBatchBox", "CheckBoxControl", True, "Use MayaBatch Plugin", 8, 1, "This uses the MayaBatch plugin. It keeps the scene loaded in memory between frames, which reduces the overhead of rendering the job.", False )
    mayaBatchBox.ValueModified.connect(MayaBatchChanged)
    scriptDialog.AddSelectionControlToGrid( "Ignore211Box", "CheckBoxControl", False, "Ignore Error Code 211", 8, 2, "This allows a MayaCmd task to finish successfully even if Maya returns the non-zero error code 211. Sometimes Maya will return this error code even after successfully saving the rendered images.", False )
    scriptDialog.AddSelectionControlToGrid( "LocalRenderingBox", "CheckBoxControl", False, "Enable Local Rendering", 9, 1, "If enabled, the frames will be rendered locally, and then copied to their final network location." )
    scriptDialog.AddSelectionControlToGrid( "StrictErrorCheckingBox", "CheckBoxControl", True, "Strict Error Checking", 9, 2, "Enable this option to have Deadline fail Maya jobs when Maya prints out any 'error' or 'warning' messages. If disabled, Deadline will only fail on messages that it knows are fatal." )
    ###################################################
    
    scriptDialog.AddControlToGrid( "RendererLabel", "LabelControl", "Renderer", 10, 0, "The Maya renderer to use. If you select 'File', the renderer defined in the scene file will be used, but renderer specific options will not be set by Deadline.", False )
    rendererBox = scriptDialog.AddComboControlToGrid( "RendererBox", "ComboControl", "Arnold", ("File","3delight","Arnold","FinalRender","Gelato","Maxwell",
                                                                                              "MayaKrakatoa","MayaHardware","MayaHardware2","MayaSoftware",
                                                                                              "MayaVector","MentalRay","OctaneRender","Redshift","Renderman",
                                                                                              "RendermanRIS","Turtle","Vray","Iray"), 10, 1 )
    rendererBox.ValueModified.connect(RendererChanged)
    
    ###################################################
    scriptDialog.AddControlToGrid( "ArnoldVerboseLabel", "LabelControl", "Arnold Verbosity", 11, 0, "Set the verbosity level for Arnold renders.", False )
    scriptDialog.AddComboControlToGrid( "ArnoldVerboseBox", "ComboControl", "1", ("0","1","2"), 11, 1 )
    ###################################################
    
    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()
    
    scriptDialog.AddTabPage("Advanced Options")
    
########################################################################
## Advanced Maya Options Tab
########################################################################

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator5", "SeparatorControl", "Advanced Maya Options", 0, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "CpusLabel", "LabelControl", "Threads", 1, 0, "The number of threads to use for rendering.", False )
    scriptDialog.AddRangeControlToGrid( "CpusBox", "RangeControl", 0, 0, 256, 0, 1, 1, 1 )
    scriptDialog.AddControlToGrid( "FrameNumberOffsetLabel", "LabelControl", "Frame Number Offset", 2, 0, "Uses Maya's frame renumbering option to offset the frames that are rendered.", False )
    scriptDialog.AddRangeControlToGrid( "FrameNumberOffsetBox", "RangeControl", 0, -100000, 100000, 0, 1, 2, 1 )
    scriptDialog.AddControlToGrid( "VersionLabel", "LabelControl", "Version", 3, 0, "The version of Maya to render with.", False )
    versionBox = scriptDialog.AddComboControlToGrid( "VersionBox", "ComboControl", "2017", ("2010","2011","2011.5","2012","2012.5"
                                                                                            ,"2013","2013.5","2014", "2014.5","2015",
                                                                                            "2015.5","2016", "2016.5", "2017", "2017.5" ), 3, 1 )
    versionBox.ValueModified.connect(VersionChanged)
    
    scriptDialog.AddSelectionControlToGrid( "SkipExistingBox", "CheckBoxControl", False, "Skip Existing Frames", 3, 2, "If enabled, Maya will skip rendering existing frames. Only supported for Maya Softwate, Maya Hardware, Maya Vector, and Mentay Ray." )

    scriptDialog.AddControlToGrid( "StartupScriptLabel", "LabelControl", "Startup Script", 4, 0, "Maya will source the specified script file on startup.", False )
    scriptDialog.AddSelectionControlToGrid( "StartupScriptBox", "FileBrowserControl", "", "Melscript Files (*.mel);;Python Files (*.py);;All Files (*)", 4, 1, colSpan=2 )
    
    overrideSizeBox = scriptDialog.AddSelectionControlToGrid( "OverrideSizeBox", "CheckBoxControl", False, "Override Resolution", 5, 0, "Enable this option to override the Width and Height (respectively) of the rendered images.", colSpan=1)
    scriptDialog.AddRangeControlToGrid( "WidthSizeRange", "RangeControl", 0, 0, 1000000, 0, 1, 5, 1)
    scriptDialog.AddRangeControlToGrid( "HeightSizeRange", "RangeControl", 0, 0, 1000000, 0, 1, 5, 2)
    overrideSizeBox.ValueModified.connect(OverrideSizeChanged)
    OverrideSizeChanged()
    
    scaleBox = scriptDialog.AddSelectionControlToGrid( "ScaleBox", "CheckBoxControl", False, "Scale Resolution", 6, 0, "Enable this option to scale the size of the rendered images to the specified percentage.", colSpan=1)
    scriptDialog.AddRangeControlToGrid( "ScaleRange", "RangeControl", 100, 0.01, 1000, 2, 1, 6, 1)
    scaleBox.ValueModified.connect(ScaleChanged)
    ScaleChanged()

    scriptDialog.AddSelectionControlToGrid( "FileUsesLegacyRenderLayersBox", "CheckBoxControl", False, "File Uses Legacy Render Layers", 6, 2, "As of Maya 2016.5, Autodesk has added a new render layer system (render setup) that is incompatible with the older version (legacy). This value specifies which render layers system this file uses." )
    
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator4", "SeparatorControl", "Command Line Options", 0, 0, colSpan=2 )

    scriptDialog.AddControlToGrid( "CommandLineLabel", "LabelControl", "Additional Arguments", 1, 0, "Specify additional command line arguments you would like to pass to the renderer.", False )
    scriptDialog.AddControlToGrid( "CommandLineBox", "TextControl", "", 1, 1 )

    scriptDialog.AddSelectionControlToGrid( "UseCommandLineBox", "CheckBoxControl", False, "Use Only Additional Command Line Arguments", 2, 0, "Enable this option to only use the command line arguments specified above when rendering.", colSpan=2 )

    scriptDialog.AddControlToGrid( "Separator7", "SeparatorControl", "Script Job Options", 3, 0, colSpan=2 )
    scriptDialog.AddControlToGrid( "ScriptJobLabel1", "LabelControl", "Script Jobs use the MayaBatch plugin, and do not force a particular render.", 4, 0, colSpan=2 )
    scriptJobBox = scriptDialog.AddSelectionControlToGrid( "ScriptJobBox", "CheckBoxControl", False, "Submit A Maya Script Job (melscript or python)", 5, 0, "Enable this option to submit a custom melscript or python script job. This script will be applied to the scene file that is specified.", colSpan=2 )
    scriptJobBox.ValueModified.connect(ScriptJobChanged)

    scriptDialog.AddControlToGrid( "ScriptFileLabel", "LabelControl", "Script File", 6, 0, "The script file to use.", False )
    scriptDialog.AddSelectionControlToGrid( "ScriptFileBox", "FileBrowserControl", "", "Maya Script Files (*.mel *.py)", 6, 1 )

    scriptDialog.AddControlToGrid( "ScriptJobLabel2", "LabelControl", "All other options on this tab page are ignored, except for the Strict Error Checking option.", 7, 0, colSpan=2 )
    
    scriptDialog.EndGrid()
    
    scriptDialog.EndTabPage()
    
########################################################################
## "Renderer Options Tab
########################################################################
    
    scriptDialog.AddTabPage( "Renderer Options" )
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid("ROHSpacer1", 1, 2)

    scriptDialog.AddControlToGrid( "MentalRaySeparator", "SeparatorControl", "Mental Ray Options", 2, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "MentalRayVerboseLabel", "LabelControl", "Mental Ray Verbosity", 3, 0, "Set the verbosity level for Mental Ray renders.", False )
    scriptDialog.AddComboControlToGrid( "MentalRayVerboseBox", "ComboControl", "Progress Messages", ("No Messages","Fatal Messages Only","Error Messages","Warning Messages","Info Messages","Progress Messages","Detailed Messages (Debug)"), 3, 1 )

    autoMemoryLimitBox = scriptDialog.AddSelectionControlToGrid( "AutoMemoryLimitBox", "CheckBoxControl", True, "Auto Memory Limit", 4, 0, "If enabled, Mental Ray will automatically detect the optimal memory limit when rendering.", False )
    autoMemoryLimitBox.ValueModified.connect(AutoMemoryLimitChanged)

    scriptDialog.AddControlToGrid( "MemoryLimitLabel", "LabelControl", "Memory Limit (in MB)", 5, 0, "Soft limit (in MB) for the memory used by Mental Ray (specify 0 for unlimited memory).", False )
    scriptDialog.AddRangeControlToGrid( "MemoryLimitBox", "RangeControl", 0, 0, 100000, 0, 1, 5, 1 )

    scriptDialog.AddControlToGrid( "RedshiftSeparator", "SeparatorControl", "Redshift Options", 6, 0, colSpan=3 )

    scriptDialog.AddControlToGrid( "RedshiftGPUsPerTaskLabel", "LabelControl", "GPUs Per Task", 7, 0, "The number of GPUs to use per task. If set to 0, the default number of GPUs will be used, unless 'Select GPU Devices' Id's have been defined.", False )
    redshiftGPUsPerTaskBox = scriptDialog.AddRangeControlToGrid( "RedshiftGPUsPerTaskBox", "RangeControl", 0, 0, 1024, 0, 1, 7, 1 )
    redshiftGPUsPerTaskBox.ValueModified.connect(RedshiftGPUsPerTaskChanged)

    scriptDialog.AddControlToGrid( "RedshiftGPUsSelectDevicesLabel", "LabelControl", "Select GPU Devices", 8, 0, "A comma separated list of the GPU devices to use specified by device Id. 'GPUs Per Task' will be ignored.", False )
    redshiftGPUsSelectDevicesBox = scriptDialog.AddControlToGrid( "RedshiftGPUsSelectDevicesBox", "TextControl", "", 8, 1 )
    redshiftGPUsSelectDevicesBox.ValueModified.connect(RedshiftGPUsSelectDevicesChanged)

    scriptDialog.AddControlToGrid( "VRaySeparator", "SeparatorControl", "VRay Options", 9, 0, colSpan=3 )

    vrayAutoMemoryBox = scriptDialog.AddSelectionControlToGrid( "VRayAutoMemoryBox", "CheckBoxControl", False, "Auto Memory Limit Detection (Requires the MayaBatch Plugin)", 10, 0, "If enabled, Deadline will automatically detect the dynamic memory limit for VRay prior to rendering.", colSpan=2 )
    vrayAutoMemoryBox.ValueModified.connect(VRayAutoMemoryChanged)

    scriptDialog.AddControlToGrid( "VRayMemoryLimitLabel", "LabelControl", "Memory Buffer (in MB)", 11, 0, "Deadline subtracts this value from the system's unused memory to determine the dynamic memory limit for VRay.", False )
    scriptDialog.AddRangeControlToGrid( "VRayMemoryLimitBox", "RangeControl", 500, 0, 100000, 0, 1, 11, 1 )
    
    scriptDialog.AddControlToGrid( "IRaySeparator", "SeparatorControl", "IRay Options", 12, 0, colSpan=3 )
    
    scriptDialog.AddControlToGrid( "IRayGPUsPerTaskLabel", "LabelControl", "GPUs Per Task", 13, 0, "The number of GPUs to use per task. If set to 0, the default number of GPUs will be used, unless 'Select GPU Devices' Id's have been defined.", False )
    irayGPUsPerTaskBox = scriptDialog.AddRangeControlToGrid( "IRayGPUsPerTaskBox", "RangeControl", 0, 0, 1024, 0, 1, 13, 1 )
    irayGPUsPerTaskBox.ValueModified.connect(IRayGPUsPerTaskChanged)

    scriptDialog.AddControlToGrid( "IRayGPUsSelectDevicesLabel", "LabelControl", "Select GPU Devices", 14, 0, "A comma separated list of the GPU devices to use specified by device Id. 'GPUs Per Task' will be ignored.", False )
    irayGPUsSelectDevicesBox = scriptDialog.AddControlToGrid( "IRayGPUsSelectDevicesBox", "TextControl", "", 14, 1 )
    irayGPUsSelectDevicesBox.ValueModified.connect(IRayGPUsSelectDevicesChanged)
    
    irayUseCPUsBox = scriptDialog.AddSelectionControlToGrid( "IRayUseCPUsBox", "CheckBoxControl", True, "Render Using CPUs", 15, 0, "If enabled, CPUs will be used to render the scene in addition to GPUs." )
    irayUseCPUsBox.ValueModified.connect(IRayUseCPUsChanged)
    scriptDialog.AddControlToGrid( "IRayCPULoadLabel", "LabelControl", "CPU Load", 15, 1, "The maximum load on the CPU for each task.", False )
    scriptDialog.AddRangeControlToGrid( "IRayCPULoadBox", "RangeControl", 1.0, 4.0, 8, 1, 0.1, 15, 2 )
    
    scriptDialog.AddControlToGrid( "IRayMaxSamplesLabel", "LabelControl", "Max Samples", 16, 0, "The Maximum number of samples per frame.", False )
    scriptDialog.AddRangeControlToGrid( "IRayMaxSamplesBox", "RangeControl", 1, 1, 4096, 0, 1, 16, 1 )
    
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
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer1", 0, 0 )
    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()
    
###################################################################################################################################    
###################################################################################################################################  

    settings = ("PoolBox","SecondaryPoolBox","GroupBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    if args:
        print "TESTING"
        for arg in args:
            print arg
        
        scriptDialog.SetValue( "SceneBox", args[0] )
        scriptDialog.SetValue( "FramesBox", args[1] )
        scriptDialog.SetValue( "OutputBox", args[2] )
        scriptDialog.SetValue( "FileTypeBox", args[3] )
        scriptDialog.SetValue( "ProjectCodeBox", args[4] )
        scriptDialog.SetValue( "ProjectPhaseBox", args[5] )
        scriptDialog.SetValue( "VersionBox", args[6] )    
        scriptDialog.SetValue( "FrameSizeBox", args[7] )    
        scriptDialog.SetValue( "ProjectBox", args[8] )
        cameras = args[9].split(",")
        scriptDialog.SetItems( "CameraBox", cameras )
        scriptDialog.SetValue( "CameraBox", cameras[0] )
        sceneName = Path.GetFileName( args[0] )
        jobName = sceneName[:-4]
        scriptDialog.SetValue( "NameBox", jobName )
    
###################################################################################################################################    
###################################################################################################################################
    
    RedshiftGPUsPerTaskChanged()
    RedshiftGPUsSelectDevicesChanged()
    IRayGPUsPerTaskChanged()
    IRayGPUsSelectDevicesChanged()
    IRayUseCPUsChanged()
    VersionChanged()
    RendererChanged()
    MayaBatchChanged()
    AutoMemoryLimitChanged()
    VRayAutoMemoryChanged()
    
    ScriptJobChanged()
    
    LoadIntegrationSettings()
    updateDisplay()
    scriptDialog.SetValue("CreateVersionBox",False)
        
    scriptDialog.ShowDialog( False )
    
def SetDefaultLocation():
    global defaultLocation
    global scriptDialog
    global sceneBox
    global outputBox
    
    defaultLocation = scriptDialog.GetValue( "ProjectBox" )
    
    sceneLocation = os.path.join(defaultLocation, "scenes")
    outputLocation = os.path.join(defaultLocation, "images")
    
    if not os.path.exists(sceneLocation):
        sceneLocation = defaultLocation
    if not os.path.exists(outputLocation):
        outputLocation = defaultLocation
    
    outputBox.setBrowserLocation( outputLocation )
    sceneBox.setBrowserLocation( sceneLocation )
      
def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "MayaSettings.ini" )

def ConnectButtonPressed( *args ):
    global scriptDialog
    script = ""
    settingsName = ""
    integration = scriptDialog.GetValue("IntegrationTypeBox")
    
    if integration == "Shotgun":
        script = Path.Combine( RepositoryUtils.GetRootDirectory("events/Shotgun"), "ShotgunUI.py" )
        settingsName = GetShotgunSettingsFilename()
    elif integration == "FTrack":
        script = Path.Combine( RepositoryUtils.GetRootDirectory("submission/FTrack/Main"), "FTrackUI.py" )
        settingsName = GetFTrackSettingsFilename()
    else:
        script = Path.Combine( RepositoryUtils.GetRootDirectory("events/NIM"), "NIM_UI.py" )
        settingsName = GetNimSettingsFilename()
        
    args = ["-ExecuteScript", script, "MayaMonitor"]
    args += AdditionalArgs()
        
    output = ClientUtils.ExecuteCommandAndGetOutput( args )
    updated = ProcessLines( output.splitlines(), integration )
    if updated:
        File.WriteAllLines( settingsName, tuple(output.splitlines()) )
        updateDisplay()
        
def AdditionalArgs():
    integration = scriptDialog.GetValue("IntegrationTypeBox")
    additionalArgs = []
    
    if integration == "Shotgun":
        if 'UserName' in shotgunSettings:
            userName = shotgunSettings['UserName']
            if userName != None and len(userName) > 0:
                additionalArgs.append("UserName="+str(userName))
                
        if 'VersionName' in shotgunSettings:
            versionName = shotgunSettings['VersionName']
            if versionName != None and len(versionName) > 0:
                additionalArgs.append("VersionName="+str(versionName))
                
        if 'TaskName' in shotgunSettings:
            taskName = shotgunSettings['TaskName']
            if taskName != None and len(taskName) > 0:
                additionalArgs.append("TaskName="+str(taskName))
                
        if 'ProjectName' in shotgunSettings:
            projectName = shotgunSettings['ProjectName']
            if projectName != None and len(projectName) > 0:
                additionalArgs.append("ProjectName="+str(projectName))
                
        if 'EntityName' in shotgunSettings:
            entityName = shotgunSettings['EntityName']
            if entityName != None and len(entityName) > 0:
                additionalArgs.append("EntityName="+str(entityName))
                
        if 'EntityType' in shotgunSettings:
            entityType = shotgunSettings['EntityType']
            if entityType != None and len(entityType) > 0:
                additionalArgs.append("EntityType="+str(entityType))
                
    elif integration == "FTrack":
        if 'FT_Username' in fTrackSettings:
            userName = fTrackSettings['FT_Username']
            if userName != None and len(userName) > 0:
                additionalArgs.append("UserName="+str(userName))
                
        if 'FT_TaskName' in fTrackSettings:
            taskName = fTrackSettings['FT_TaskName']
            if taskName != None and len(taskName) > 0:
                additionalArgs.append("TaskName="+str(taskName))
                
        if 'FT_ProjectName' in fTrackSettings:
            projectName = fTrackSettings['FT_ProjectName']
            if projectName != None and len(projectName) > 0:
                additionalArgs.append("ProjectName="+str(projectName))
                
        if 'FT_AssetName' in fTrackSettings:
            assetName = fTrackSettings['FT_AssetName']
            if assetName != None and len(assetName) > 0:
                additionalArgs.append("AssetName="+str(assetName))

    return additionalArgs
    
def ProcessLines( lines, integration ):
    global shotgunSettings
    global fTrackSettings
    global nimSettings
    
    tempKVPs = {}
    
    for line in lines:
        line = line.strip()
        tokens = line.split( '=', 1 )
        
        if len( tokens ) > 1:
            key = tokens[0]
            value = tokens[1]
            tempKVPs[key] = value
    
    if len(tempKVPs)>0:
        if integration == "Shotgun":
            shotgunSettings = tempKVPs
        elif integration == "FTrack":
            fTrackSettings = tempKVPs
        else:
            nimSettings = tempKVPs
            
        return True
    
    return False
                           
def updateDisplay():
    global fTrackSettings
    global shotgunSettings
    global nimSettings
    
    integration = scriptDialog.GetValue("IntegrationTypeBox")
    
    displayText = ""
    if integration == "Shotgun":
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
    elif integration == "FTrack":
        if 'FT_Username' in fTrackSettings:
            displayText += "User Name: %s\n" % fTrackSettings[ 'FT_Username' ]
        if 'FT_TaskName' in fTrackSettings:
            displayText += "Task Name: %s\n" % fTrackSettings[ 'FT_TaskName' ]
        if 'FT_ProjectName' in fTrackSettings:
            displayText += "Project Name: %s\n" % fTrackSettings[ 'FT_ProjectName' ]
    
        scriptDialog.SetValue( "IntegrationEntityInfoBox", displayText )
        scriptDialog.SetValue( "IntegrationVersionBox", fTrackSettings.get( 'FT_AssetName', "" ) )
        scriptDialog.SetValue( "IntegrationDescriptionBox", fTrackSettings.get( 'FT_Description', "" ) )
    else:
        if 'nim_useNim' in nimSettings:
            displayText += "Use Nim: %s\n" % nimSettings[ 'nim_useNim' ]
        if 'nim_basename' in nimSettings:
            displayText += "Basename: %s\n" % nimSettings[ 'nim_basename' ]
        if 'nim_jobName' in nimSettings:
            displayText += "Job Name: %s\n" % nimSettings[ 'nim_jobName' ]
        if 'nim_class' in nimSettings:
            displayText += "Class: %s\n" % nimSettings[ 'nim_class' ]
        if 'nim_assetName' in nimSettings:
            displayText += "Asset Name: %s\n" % nimSettings[ 'nim_assetName' ]
        if 'nim_showName' in nimSettings:
            displayText += "Show Name: %s\n" % nimSettings[ 'nim_showName' ]
        if 'nim_shotName' in nimSettings:
            displayText += "Shot Name: %s\n" % nimSettings[ 'nim_shotName' ]
        if 'nim_taskID' in nimSettings:
            displayText += "Task ID: %s\n" % nimSettings[ 'nim_taskID' ]
        if 'nim_itemID' in nimSettings:
            displayText += "Item ID: %s\n" % nimSettings[ 'nim_itemID' ]
        if 'nim_jobID' in nimSettings:
            displayText += "Job ID: %s\n" % nimSettings[ 'nim_jobID' ]
        if 'nim_fileID' in nimSettings:
            displayText += "File ID: %s\n" % nimSettings[ 'nim_fileID' ]
            
        scriptDialog.SetValue( "IntegrationEntityInfoBox", displayText )
        scriptDialog.SetValue( "IntegrationVersionBox", nimSettings.get( 'nim_renderName', "" ) )
        scriptDialog.SetValue( "IntegrationDescriptionBox", nimSettings.get( 'nim_description', "" ) )
        
    if len(displayText)>0:
        scriptDialog.SetEnabled("CreateVersionBox",True)
        scriptDialog.SetValue("CreateVersionBox",True)
    else:
        scriptDialog.SetEnabled("CreateVersionBox",False)
        scriptDialog.SetValue("CreateVersionBox",False)

def LoadIntegrationSettings():
    global fTrackSettings
    global shotgunSettings
    global nimSettings
    
    fTrackSettings = {}
    shotgunSettings = {}
    nimSettings = {}
        
    settingsFile = GetShotgunSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), "Shotgun" )
        
    settingsFile = GetFTrackSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), "FTrack" )
        
    settingsFile = GetNimSettingsFilename()
    if File.Exists( settingsFile ):
        ProcessLines( File.ReadAllLines( settingsFile ), "NIM" )

def IntegrationTypeBoxChanged():
    updateDisplay()
    
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun") and scriptDialog.GetValue( "CreateVersionBox" )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", shotgunEnabled )
    
def GetShotgunSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "MayaMonitorSettingsShotgun.ini" )

def GetFTrackSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "MayaMonitorSettingsFTrack.ini" )

def GetNimSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "AfterEffectsMonitorSettingsNim.ini" )
    
def SubmitShotgunChanged( *args ):
    global scriptDialog
    
    integrationEnabled = scriptDialog.GetValue( "CreateVersionBox" )
    shotgunEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "Shotgun")
    ftrackEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "FTrack")
    nimEnabled = (scriptDialog.GetValue("IntegrationTypeBox") == "NIM")
    
    scriptDialog.SetEnabled( "IntegrationVersionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationVersionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationDescriptionBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoLabel", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationEntityInfoBox", integrationEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadMovieBox", integrationEnabled and not nimEnabled )
    scriptDialog.SetEnabled( "IntegrationUploadFilmStripBox", integrationEnabled and shotgunEnabled )

def VersionChanged(*args):
    global scriptDialog
    
    renderer = scriptDialog.GetValue( "RendererBox" )
    skipExistingEnabled = (float(scriptDialog.GetValue( "VersionBox" )) >= 2014) and (renderer == "MayaHardware" or renderer == "MayaHardware2" or renderer == "MayaVector" or renderer == "MayaSoftware" or renderer == "MentalRay")
    scriptDialog.SetEnabled( "SkipExistingBox", skipExistingEnabled )

    legacyRenderLayersEnabled = float( scriptDialog.GetValue( "VersionBox" ) ) >= 2016.5
    scriptDialog.SetEnabled( "FileUsesLegacyRenderLayersBox", legacyRenderLayersEnabled )

def RendererChanged(*args):
    global scriptDialog

    enabled = ( scriptDialog.GetValue( "RendererBox" ) != "3delight" )
    scriptDialog.SetEnabled( "OutputLabel", enabled )
    scriptDialog.SetEnabled( "OutputBox", enabled )

    renderer = scriptDialog.GetValue("RendererBox" )
    threadsEnabled = (renderer == "MayaSoftware" or renderer == "MentalRay" or renderer == "Renderman" or renderer == "RendermanRIS" or renderer == "3delight" or renderer == "FinalRender" or renderer == "Maxwell" or renderer == "Vray")
    scriptDialog.SetEnabled( "CpusLabel", threadsEnabled )
    scriptDialog.SetEnabled( "CpusBox", threadsEnabled )

    fileEnabled = not (renderer == "File")
    scriptDialog.SetEnabled( "FrameNumberOffsetLabel", fileEnabled )
    scriptDialog.SetEnabled( "FrameNumberOffsetBox", fileEnabled )
    scriptDialog.SetEnabled( "OverrideSizeBox", fileEnabled )

    arEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "Arnold" )
    # scriptDialog.SetEnabled( "ArnoldSeparator", arEnabled )
    scriptDialog.SetEnabled( "ArnoldVerboseLabel", arEnabled )
    scriptDialog.SetEnabled( "ArnoldVerboseBox", arEnabled )

    mrEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "MentalRay" )
    scriptDialog.SetEnabled( "MentalRaySeparator", mrEnabled )
    scriptDialog.SetEnabled( "MentalRayVerboseLabel", mrEnabled )
    scriptDialog.SetEnabled( "MentalRayVerboseBox", mrEnabled )
    scriptDialog.SetEnabled( "AutoMemoryLimitBox", mrEnabled )

    mlEnabled = not scriptDialog.GetValue( "AutoMemoryLimitBox" )
    scriptDialog.SetEnabled( "MemoryLimitLabel", mrEnabled and mlEnabled )
    scriptDialog.SetEnabled( "MemoryLimitBox", mrEnabled and mlEnabled )

    vrayEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "Vray" )
    batchEnabled = scriptDialog.GetValue( "MayaBatchBox" )
    memEnabled = scriptDialog.GetValue( "VRayAutoMemoryBox" )
    scriptDialog.SetEnabled( "VRaySeparator", vrayEnabled )
    scriptDialog.SetEnabled( "VRayAutoMemoryBox", vrayEnabled and batchEnabled )
    scriptDialog.SetEnabled( "VRayMemoryLimitLabel", vrayEnabled and memEnabled and batchEnabled )
    scriptDialog.SetEnabled( "VRayMemoryLimitBox", vrayEnabled and memEnabled and batchEnabled )

    redshiftEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "Redshift" )
    scriptDialog.SetEnabled( "RedshiftSeparator", redshiftEnabled )
    scriptDialog.SetEnabled( "RedshiftGPUsPerTaskLabel", redshiftEnabled )
    scriptDialog.SetEnabled( "RedshiftGPUsPerTaskBox", redshiftEnabled )
    scriptDialog.SetEnabled( "RedshiftGPUsSelectDevicesLabel", redshiftEnabled )
    scriptDialog.SetEnabled( "RedshiftGPUsSelectDevicesBox", redshiftEnabled )
    
    irayEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "Iray" )
    scriptDialog.SetEnabled( "IRaySeparator", irayEnabled )
    scriptDialog.SetEnabled( "IRayGPUsPerTaskLabel", irayEnabled )
    scriptDialog.SetEnabled( "IRayGPUsPerTaskBox", irayEnabled )
    scriptDialog.SetEnabled( "IRayGPUsSelectDevicesLabel", irayEnabled )
    scriptDialog.SetEnabled( "IRayGPUsSelectDevicesBox", irayEnabled )
    scriptDialog.SetEnabled( "IRayUseCPUsBox", irayEnabled )
    scriptDialog.SetEnabled( "IRayCPULoadLabel", irayEnabled )
    scriptDialog.SetEnabled( "IRayCPULoadBox", irayEnabled )
    scriptDialog.SetEnabled( "IRayMaxSamplesLabel", irayEnabled )
    scriptDialog.SetEnabled( "IRayMaxSamplesBox", irayEnabled )

    skipExistingEnabled = (float(scriptDialog.GetValue( "VersionBox" )) >= 2014) and (renderer == "MayaHardware" or renderer == "MayaHardware2" or renderer == "MayaVector" or renderer == "MayaSoftware" or renderer == "MentalRay")
    scriptDialog.SetEnabled( "SkipExistingBox", skipExistingEnabled )
    
def MayaBatchChanged(*args):
    global scriptDialog
    
    batchEnabled = scriptDialog.GetValue( "MayaBatchBox" )
    scriptDialog.SetEnabled( "Ignore211Box", not batchEnabled )
    scriptDialog.SetEnabled( "StartupScriptLabel", batchEnabled )
    scriptDialog.SetEnabled( "StartupScriptBox", batchEnabled )
    scriptDialog.SetEnabled( "Separator4", not batchEnabled )
    scriptDialog.SetEnabled( "CommandLineLabel", not batchEnabled )
    scriptDialog.SetEnabled( "CommandLineBox", not batchEnabled )
    scriptDialog.SetEnabled( "UseCommandLineBox", not batchEnabled )
    
    vrayEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "Vray" )
    memEnabled = scriptDialog.GetValue( "VRayAutoMemoryBox" )
    scriptDialog.SetEnabled( "VRayAutoMemoryBox", vrayEnabled and batchEnabled )
    scriptDialog.SetEnabled( "VRayMemoryLimitLabel", vrayEnabled and memEnabled and batchEnabled )
    scriptDialog.SetEnabled( "VRayMemoryLimitBox", vrayEnabled and memEnabled and batchEnabled )
    
def AutoMemoryLimitChanged(*args):
    global scriptDialog
    
    mlEnabled = not scriptDialog.GetValue( "AutoMemoryLimitBox" )
    mrEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "MentalRay" )
    
    scriptDialog.SetEnabled( "MemoryLimitLabel", mrEnabled and mlEnabled )
    scriptDialog.SetEnabled( "MemoryLimitBox", mrEnabled and mlEnabled )

def RedshiftGPUsPerTaskChanged(*args):
    global scriptDialog

    perTaskEnabled = ( scriptDialog.GetValue( "RedshiftGPUsPerTaskBox" ) == 0 )

    scriptDialog.SetEnabled( "RedshiftGPUsSelectDevicesLabel", perTaskEnabled )
    scriptDialog.SetEnabled( "RedshiftGPUsSelectDevicesBox", perTaskEnabled )

def RedshiftGPUsSelectDevicesChanged(*args):
    global scriptDialog

    selectDeviceEnabled = ( scriptDialog.GetValue( "RedshiftGPUsSelectDevicesBox" ) == "" )

    scriptDialog.SetEnabled( "RedshiftGPUsPerTaskLabel", selectDeviceEnabled )
    scriptDialog.SetEnabled( "RedshiftGPUsPerTaskBox", selectDeviceEnabled )

def IRayGPUsPerTaskChanged(*args):
    global scriptDialog

    perTaskEnabled = ( scriptDialog.GetValue( "IRayGPUsPerTaskBox" ) == 0 )

    scriptDialog.SetEnabled( "IRayGPUsSelectDevicesLabel", perTaskEnabled )
    scriptDialog.SetEnabled( "IRayGPUsSelectDevicesBox", perTaskEnabled )

def IRayGPUsSelectDevicesChanged(*args):
    global scriptDialog

    selectDeviceEnabled = ( scriptDialog.GetValue( "IRayGPUsSelectDevicesBox" ) == "" )

    scriptDialog.SetEnabled( "IRayGPUsPerTaskLabel", selectDeviceEnabled )
    scriptDialog.SetEnabled( "IRayGPUsPerTaskBox", selectDeviceEnabled )

def IRayUseCPUsChanged(*args):
    global scriptDialog
    
    scriptDialog.SetEnabled( "IRayCPULoadBox", scriptDialog.GetValue( "IRayUseCPUsBox" ) )
 
def OverrideSizeChanged(*args):
    global scriptDialog
    overrideEnabled = scriptDialog.GetValue( "OverrideSizeBox" )
    
    scriptDialog.SetEnabled( "WidthSizeRange", overrideEnabled )
    scriptDialog.SetEnabled( "HeightSizeRange", overrideEnabled )

def ScaleChanged(*args):
    global scriptDialog
    scaleEnabled = scriptDialog.GetValue( "ScaleBox" )
    
    scriptDialog.SetEnabled( "ScaleRange", scaleEnabled )

def VRayAutoMemoryChanged(*args):
    global scriptDialog
    
    vrayEnabled = ( scriptDialog.GetValue( "RendererBox" ) == "Vray" )
    batchEnabled = scriptDialog.GetValue( "MayaBatchBox" )
    memEnabled = scriptDialog.GetValue( "VRayAutoMemoryBox" )
    
    scriptDialog.SetEnabled( "VRayMemoryLimitLabel", vrayEnabled and memEnabled and batchEnabled )
    scriptDialog.SetEnabled( "VRayMemoryLimitBox", vrayEnabled and memEnabled and batchEnabled )

def ScriptJobChanged(*args):
    global scriptDialog
    
    enabled = scriptDialog.GetValue( "ScriptJobBox" )
    scriptDialog.SetEnabled( "ScriptFileLabel", enabled )
    scriptDialog.SetEnabled( "ScriptFileBox", enabled )
    scriptDialog.SetEnabled( "ScriptJobLabel2", enabled )
    
def SubmitButtonPressed( *args ):
    global scriptDialog
    global shotgunSettings
    global fTrackSettings
    global nimSettings
    
    try:
        renderer = scriptDialog.GetValue( "RendererBox" )
        scriptJob = scriptDialog.GetValue( "ScriptJobBox" )
        
        if renderer == "Iray":
            renderer == "ifmIrayPhotoreal"
        
        # Check if maya files.
        sceneFiles = StringUtils.FromSemicolonSeparatedString( scriptDialog.GetValue( "SceneBox" ), False )
        if( len( sceneFiles ) == 0 ):
            scriptDialog.ShowMessageBox( "No Maya file specified", "Error" )
            return
        
        for sceneFile in sceneFiles:
            if( not File.Exists( sceneFile ) ):
                scriptDialog.ShowMessageBox( "Maya file %s does not exist" % sceneFile, "Error" )
                return
            #if the submit scene box is checked check if they are local, if they are warn the user
            elif( not bool( scriptDialog.GetValue("SubmitSceneBox") ) and PathUtils.IsPathLocal( sceneFile ) ):
                result = scriptDialog.ShowMessageBox( "The scene file " + sceneFile + " is local, are you sure you want to continue?", "Warning", ("Yes","No") )
                if( result == "No" ):
                    return
        
        # Check project folder.
        projectFolder = (scriptDialog.GetValue( "ProjectBox" )).strip()
        if( not Directory.Exists( projectFolder ) ):
            scriptDialog.ShowMessageBox( "Project folder %s does not exist" % projectFolder, "Error" )
            return
        elif( PathUtils.IsPathLocal( projectFolder ) ):
            result = scriptDialog.ShowMessageBox( "Project folder " + projectFolder + " is local, are you sure you want to continue?", "Warning", ("Yes","No") )
            if( result == "No" ):
                return
        
        # Check output folder.
        outputFolder = (scriptDialog.GetValue( "OutputBox" )).strip()
        if( not scriptJob and renderer != "3delight" ):
            if( not Directory.Exists( outputFolder ) ):
                scriptDialog.ShowMessageBox( "Output folder %s does not exist" % outputFolder, "Error" )
                return
            elif( PathUtils.IsPathLocal( outputFolder ) ):
                result = scriptDialog.ShowMessageBox( "Output folder " + outputFolder + " is local, are you sure you want to continue?", "Warning", ("Yes","No") )
                if( result == "No" ):
                    return
        
        # Check startup script
        startupScriptFile = scriptDialog.GetValue( "StartupScriptBox" ).strip()
        if scriptDialog.GetValue( "MayaBatchBox" ) and len(startupScriptFile) > 0:
            if( not File.Exists( startupScriptFile ) ):
                scriptDialog.ShowMessageBox( "Startup Script file %s does not exist" % startupScriptFile, "Error" )
                return
            elif ( PathUtils.IsPathLocal( startupScriptFile ) ):
                result = scriptDialog.ShowMessageBox( "Startup Script file %s is local, are you sure you want to continue?" % startupScriptFile, "Warning", ("Yes","No") )
                if( result == "No" ):
                    return
        
        # Check script
        scriptFile = (scriptDialog.GetValue( "ScriptFileBox" )).strip()
        if( scriptJob ):
            if( not File.Exists( scriptFile ) ):
                scriptDialog.ShowMessageBox( "Script file %s does not exist" % scriptFile, "Error" )
                return

        # Check if a valid frame range has been specified.
        frames = scriptDialog.GetValue( "FramesBox" )
        if( not FrameUtils.FrameRangeValid( frames ) ):
            scriptDialog.ShowMessageBox( "Frame range %s is not valid" % frames, "Error" )
            return
            
        # If Redshift and using 'select GPU device Ids' then check device Id syntax is valid
        if( renderer == "Redshift" and scriptDialog.GetValue( "RedshiftGPUsPerTaskBox" ) == 0 and scriptDialog.GetValue( "RedshiftGPUsSelectDevicesBox" ) != "" ):
            regex = re.compile( "^(\d{1,2}(,\d{1,2})*)?$" )
            validSyntax = regex.match( scriptDialog.GetValue( "RedshiftGPUsSelectDevicesBox" ) )
            if not validSyntax:
                scriptDialog.ShowMessageBox( "Redshift 'Select GPU Devices' syntax is invalid!\n\nTrailing 'commas' if present, should be removed.\n\nValid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc", "Error" )
                return

            # Check if concurrent threads > 1
            if scriptDialog.GetValue( "ConcurrentTasksBox" ) > 1:
                scriptDialog.ShowMessageBox( "If using Redshift 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1", "Error" )
                return
        
        # If IRay and using 'select GPU device Ids' then check device Id syntax is valid
        if( renderer == "ifmIrayPhotoreal" and scriptDialog.GetValue( "IRayGPUsPerTaskBox" ) == 0 and scriptDialog.GetValue( "IRayGPUsSelectDevicesBox" ) != "" ):
            regex = re.compile( "^(\d{1,2}(,\d{1,2})*)?$" )
            validSyntax = regex.match( scriptDialog.GetValue( "IRayGPUsSelectDevicesBox" ) )
            if not validSyntax:
                scriptDialog.ShowMessageBox( "IRay 'Select GPU Devices' syntax is invalid!\n\nTrailing 'commas' if present, should be removed.\n\nValid Examples: 0 or 2 or 0,1,2 or 0,3,4 etc", "Error" )
                return

            # Check if concurrent threads > 1
            if scriptDialog.GetValue( "ConcurrentTasksBox" ) > 1:
                scriptDialog.ShowMessageBox( "If using IRay 'Select GPU Devices', then 'Concurrent Tasks' must be set to 1", "Error" )
                return
        

        successes = 0
        failures = 0
        
        # Submit each scene file separately.
        for sceneFile in sceneFiles:
            # Create job info file.Fexecute
            jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "maya_job_info.job" )
            writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
            if( scriptJob or scriptDialog.GetValue( "MayaBatchBox" ) ):
                writer.WriteLine( "Plugin=MayaBatch" )
            else:
                writer.WriteLine( "Plugin=MayaCmd" )
            
            jobName = scriptDialog.GetValue( "NameBox" )
            
            if len( sceneFiles ) > 1:
                jobName = jobName + " [" + Path.GetFileName( sceneFile ) + "]"
                
            if scriptJob:
                jobName = jobName + " [Script Job]"
            
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
            
#######################################################################################

            # writer.WriteLine( "ExtraInfo6=%s" % scriptDialog.GetValue( "ProjectCodeBox" ) )
            # writer.WriteLine( "ExtraInfo7=%s" % scriptDialog.GetValue( "ProjectPhaseBox" ) )
            # writer.WriteLine( "ExtraInfo8=%s" % scriptDialog.GetValue( "FrameSizeBox" ) )
            # writer.WriteLine( "ExtraInfo9=%s" % scriptDialog.GetValue( "FileTypeBox" ) )
            
#######################################################################################
            
            writer.WriteLine( "MachineLimit=%s" % scriptDialog.GetValue( "MachineLimitBox" ) )
            if( bool(scriptDialog.GetValue( "IsBlacklistBox" )) ):
                writer.WriteLine( "Blacklist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            else:
                writer.WriteLine( "Whitelist=%s" % scriptDialog.GetValue( "MachineListBox" ) )
            
            writer.WriteLine( "LimitGroups=%s" % scriptDialog.GetValue( "LimitGroupBox" ) )
            writer.WriteLine( "JobDependencies=%s" % scriptDialog.GetValue( "DependencyBox" ) )
            writer.WriteLine( "OnJobComplete=%s" % scriptDialog.GetValue( "OnJobCompleteBox" ) )
            
            if( bool(scriptDialog.GetValue( "SubmitSuspendedBox" )) ):
                writer.WriteLine( "InitialStatus=Suspended" )
            
            writer.WriteLine( "Frames=%s" % frames )
            writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
            
            if( not scriptJob and renderer != "3delight" ):
                writer.WriteLine( "OutputDirectory0=%s" % outputFolder )
            
            #Shotgun
            integration = scriptDialog.GetValue( "IntegrationTypeBox" ) 
            extraKVPIndex = 0
            groupBatch = False
            if scriptDialog.GetValue( "CreateVersionBox" ):
                if integration == "Shotgun":
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
                elif integration == "FTrack":
                    writer.WriteLine( "ExtraInfo0=%s\n" % fTrackSettings.get('FT_TaskName', "") )
                    writer.WriteLine( "ExtraInfo1=%s\n" % fTrackSettings.get('FT_ProjectName', "") )
                    writer.WriteLine( "ExtraInfo2=%s\n" % scriptDialog.GetValue( "IntegrationVersionBox" ) )
                    writer.WriteLine( "ExtraInfo4=%s\n" % scriptDialog.GetValue( "IntegrationDescriptionBox" ) )
                    writer.WriteLine( "ExtraInfo5=%s\n" % fTrackSettings.get('FT_Username', "") )
                    for key in fTrackSettings:
                        writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, fTrackSettings[key]) )
                        extraKVPIndex += 1
                    if scriptDialog.GetValue("IntegrationUploadMovieBox"):
                        writer.WriteLine( "ExtraInfoKeyValue%s=Draft_CreateFTMovie=True\n" % (extraKVPIndex) )
                        extraKVPIndex += 1
                        groupBatch = True
                else:
                    writer.WriteLine( "ExtraInfo0=%s\n" % scriptDialog.GetValue( "IntegrationVersionBox" ) )
                    writer.WriteLine( "ExtraInfo1=%s\n" % nimSettings.get('nim_jobName', "") )
                    writer.WriteLine( "ExtraInfo2=%s\n" % nimSettings.get('nim_showName', "") )
                    writer.WriteLine( "ExtraInfo3=%s\n" % nimSettings.get('nim_shotName', "") )
                    writer.WriteLine( "ExtraInfo4=%s\n" % scriptDialog.GetValue( "IntegrationDescriptionBox" ) )
                    writer.WriteLine( "ExtraInfo5=%s\n" % nimSettings.get('nim_user', "") )
                    for key in nimSettings:
                        writer.WriteLine( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, nimSettings[key]) )
                        extraKVPIndex += 1
                        
            if groupBatch:
                writer.WriteLine( "BatchName=%s\n" % (jobName ) ) 
            writer.Close()
            
            # Create plugin info file.
            pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "maya_plugin_info.job" )
            writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
            
            if( not bool(scriptDialog.GetValue( "SubmitSceneBox" )) ):
                writer.WriteLine( "SceneFile=%s" % sceneFile )
            
            writer.WriteLine( "Version=%s" % scriptDialog.GetValue( "VersionBox" ) )
            writer.WriteLine( "Build=%s" % scriptDialog.GetValue( "BuildBox" ) )
            writer.WriteLine( "ProjectPath=%s" % projectFolder )
            writer.WriteLine( "StrictErrorChecking=%s" % scriptDialog.GetValue( "StrictErrorCheckingBox" ) )
            writer.WriteLine( "UseLegacyRenderLayers=%s" % int( scriptDialog.GetValue( "FileUsesLegacyRenderLayersBox" ) ) )
            
            if scriptJob:
                writer.WriteLine( "ScriptJob=True" )
                writer.WriteLine( "ScriptFilename=%s" % Path.GetFileName( scriptFile ) )
            else:
                writer.WriteLine( "LocalRendering=%s" % scriptDialog.GetValue( "LocalRenderingBox" ) )
                writer.WriteLine( "MaxProcessors=%s" % scriptDialog.GetValue( "CpusBox" ) )
                writer.WriteLine( "FrameNumberOffset=%s" % scriptDialog.GetValue( "FrameNumberOffsetBox" ) )
                
                if( renderer != "3delight" ):
                    writer.WriteLine( "OutputFilePath=%s" % outputFolder )
                
                writer.WriteLine( "Renderer=%s" % renderer )
                if( renderer == "Arnold" ):
                    writer.WriteLine( "ArnoldVerbose=%s" % scriptDialog.GetValue( "ArnoldVerboseBox" ) )
                elif( renderer == "MentalRay" ):
                    writer.WriteLine( "MentalRayVerbose=%s" % scriptDialog.GetValue( "MentalRayVerboseBox" ) )
                    writer.WriteLine( "AutoMemoryLimit=%s" % scriptDialog.GetValue( "AutoMemoryLimitBox" ) )
                    writer.WriteLine( "MemoryLimit=%s" % scriptDialog.GetValue( "MemoryLimitBox" ) )
                elif( renderer == "Vray" and scriptDialog.GetValue( "MayaBatchBox" ) ):
                    writer.WriteLine( "VRayAutoMemoryEnabled=%s" % scriptDialog.GetValue( "VRayAutoMemoryBox" ) )
                    writer.WriteLine( "VRayAutoMemoryBuffer=%s" % scriptDialog.GetValue( "VRayMemoryLimitBox" ) )
                elif( renderer == "Redshift" ):
                    writer.WriteLine( "RedshiftGPUsPerTask=%s" % scriptDialog.GetValue( "RedshiftGPUsPerTaskBox" ) )
                    writer.WriteLine( "RedshiftGPUsSelectDevices=%s" % scriptDialog.GetValue( "RedshiftGPUsSelectDevicesBox" ) )
                elif( renderer == "ifmIrayPhotoreal" ):
                    writer.WriteLine( "IRayGPUsPerTask=%s" % scriptDialog.GetValue( "IRayGPUsPerTaskBox" ) )
                    writer.WriteLine( "IRayGPUsSelectDevices=%s" % scriptDialog.GetValue( "IRayGPUsSelectDevicesBox" ) )
                    writer.WriteLine( "IRayUseCPUs=%s" % scriptDialog.GetValue( "IRayUseCPUsBox" ) )
                    writer.WriteLine( "IRayCPULoad=%s" % scriptDialog.GetValue( "IRayCPULoadBox" ) )
                    writer.WriteLine( "IRayMaxSamples=%s" % scriptDialog.GetValue( "IRayMaxSamplesBox" ) )
                
                if scriptDialog.GetValue( "MayaBatchBox" ):
                    writer.WriteLine( "StartupScript=%s" % startupScriptFile )
                
                writer.WriteLine( "CommandLineOptions=%s" % scriptDialog.GetValue( "CommandLineBox" ).strip() )
                writer.WriteLine( "UseOnlyCommandLineOptions=%d" % scriptDialog.GetValue( "UseCommandLineBox" ) )
                writer.WriteLine( "IgnoreError211=%s" % scriptDialog.GetValue( "Ignore211Box" ) )
                
                if (float(scriptDialog.GetValue( "VersionBox" )) >= 2014) and (renderer == "MayaHardware" or renderer == "MayaHardware2" or renderer == "MayaVector" or renderer == "MayaSoftware" or renderer == "MentalRay"):
                    writer.WriteLine( "SkipExistingFrames=%s" % scriptDialog.GetValue( "SkipExistingBox" ) )
                    
                if scriptDialog.GetValue( "OverrideSizeBox" ):
                    writer.WriteLine( "ImageWidth=%s" % scriptDialog.GetValue( "WidthSizeRange" ) )
                    writer.WriteLine( "ImageHeight=%s" % scriptDialog.GetValue( "HeightSizeRange" ) )
                
                if scriptDialog.GetValue( "ScaleBox" ):
                    writer.WriteLine( "ImageScale=%s" % scriptDialog.GetValue( "ScaleRange" ) )
            
            ##########################################################
            
                # if scriptDialog.GetValue( "CameraBox" ):
                #     writer.WriteLine( "Camera=%s" % scriptDialog.GetValue( "CameraBox" ) )
                    
            ##########################################################
                
            writer.Close()
            
            # Setup the command line arguments.
            arguments = StringCollection()
            #if( len( sceneFiles ) == 1 ):
            #    arguments.Add( "-notify" )
            
            arguments.Add( jobInfoFilename )
            arguments.Add( pluginInfoFilename )
            if scriptDialog.GetValue( "SubmitSceneBox" ):
                arguments.Add( sceneFile )
            if scriptJob:
                arguments.Add( scriptFile )
            
            if( len( sceneFiles ) == 1 ):
                results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
                scriptDialog.ShowMessageBox( results, "Submission Results" )
            else:
                # Now submit the job.
                exitCode = ClientUtils.ExecuteCommand( arguments )
                if( exitCode == 0 ):
                    successes = successes + 1
                else:
                    failures = failures + 1
            
        if( len( sceneFiles ) > 1 ):
            scriptDialog.ShowMessageBox( "Jobs submitted successfully: %d\nJobs not submitted: %d" % (successes, failures), "Submission Results" )
    except:
        ClientUtils.LogText( str(traceback.format_exc()) )
