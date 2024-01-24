import os, shutil
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

startup = True
updatingOutputFile = False
fileSeqs = []
userInitials = ""
pluginName = ""
jobSceneName = ""
fileDirectory = ""
frameSize = ""
projectPhase = ""
passNamesString = ""
originalInput = ""


########################################################################
## Main Function Called By Deadline
########################################################################
def __main__(*args):
    global scriptDialog
    global settings
    global startup
    global fileSeq
    global userInitials
    global pluginName
    global jobSceneName
    global fileDirectory
    global frameSize
    global frameList
    global projectPhase
    global passNamesString
    global originalInput



    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle("Submit FFmpeg Job To Deadline")
    scriptDialog.SetIcon(scriptDialog.GetIcon('FFmpeg'))

    scriptDialog.AddTabControl("Tabs", 0, 0)

    scriptDialog.AddTabPage("Job Options")
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("Separator1", "SeparatorControl",
                                  "Job Description", 0, 0)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid(
        "NameLabel", "LabelControl", "Job Name", 0, 0,
        "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.",
        False)
    scriptDialog.AddControlToGrid("NameBox", "TextControl", "Untitled", 0, 1)

    scriptDialog.AddControlToGrid(
        "CommentLabel", "LabelControl", "Comment", 1, 0,
        "A simple description of your job. This is optional and can be left blank.",
        False)
    scriptDialog.AddControlToGrid("CommentBox", "TextControl", "", 1, 1)

    scriptDialog.AddControlToGrid(
        "ProjectPhaseLabel", "LabelControl", "Project Phase", 2, 0,
        "The Project you belong to. This is optional and can be left blank.",
        False)
    scriptDialog.AddControlToGrid("ProjectPhaseBox", "TextControl", "", 2, 1)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("Separator2", "SeparatorControl",
                                  "Job Options", 0, 0)
    scriptDialog.EndGrid()

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid(
        "PoolLabel", "LabelControl", "Pool", 0, 0,
        "The pool that your job will be submitted to.", False)
    scriptDialog.AddControlToGrid("PoolBox", "PoolComboControl", "none", 0, 1)

    scriptDialog.AddControlToGrid(
        "SecondaryPoolLabel", "LabelControl", "Secondary Pool", 1, 0,
        "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Workers.",
        False)
    scriptDialog.AddControlToGrid("SecondaryPoolBox",
                                  "SecondaryPoolComboControl", "", 1, 1)

    scriptDialog.AddControlToGrid(
        "GroupLabel", "LabelControl", "Group", 2, 0,
        "The group that your job will be submitted to.", False)
    scriptDialog.AddControlToGrid("GroupBox", "GroupComboControl", "none", 2, 1)

    scriptDialog.AddControlToGrid(
        "PriorityLabel", "LabelControl", "Priority", 3, 0,
        "A job can have a numeric priority ranging from 0 to 100, where 0 is the lowest priority and 100 is the highest priority.",
        False)
    scriptDialog.AddRangeControlToGrid(
        "PriorityBox", "RangeControl",
        RepositoryUtils.GetMaximumPriority() / 2, 0,
        RepositoryUtils.GetMaximumPriority(), 0, 1, 3, 1)

    scriptDialog.AddControlToGrid(
        "TaskTimeoutLabel", "LabelControl", "Task Timeout", 4, 0,
        "The number of minutes a Worker has to render a task for this job before it requeues it. Specify 0 for no limit.",
        False)
    scriptDialog.AddRangeControlToGrid("TaskTimeoutBox", "RangeControl", 0, 0,
                                       1000000, 0, 1, 4, 1)
    scriptDialog.AddSelectionControlToGrid(
        "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout",
        4, 2,
        "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. ",
        False)

    scriptDialog.AddControlToGrid(
        "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 5, 0,
        "The number of tasks that can render concurrently on a single Worker. This is useful if the rendering application only uses one thread to render and your Workers have multiple CPUs.",
        False)
    scriptDialog.AddRangeControlToGrid("ConcurrentTasksBox", "RangeControl", 1,
                                       1, 16, 0, 1, 5, 1)
    scriptDialog.AddSelectionControlToGrid(
        "LimitConcurrentTasksBox", "CheckBoxControl", True,
        "Limit Tasks To Worker's Task Limit", 5, 2,
        "If you limit the tasks to a Worker's task limit, then by default, the Worker won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual Workers by an administrator."
    )

    scriptDialog.AddControlToGrid(
        "MachineLimitLabel", "LabelControl", "Machine Limit", 6, 0,
        "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.",
        False)
    scriptDialog.AddRangeControlToGrid("MachineLimitBox", "RangeControl", 0, 0,
                                       1000000, 0, 1, 6, 1)
    scriptDialog.AddSelectionControlToGrid(
        "IsBlacklistBox", "CheckBoxControl", False,
        "Machine List Is A Blacklist", 6, 2,
        "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist."
    )

    scriptDialog.AddControlToGrid(
        "MachineListLabel", "LabelControl", "Machine List", 7, 0,
        "The whitelisted or blacklisted list of machines.", False)
    scriptDialog.AddControlToGrid("MachineListBox",
                                  "MachineListControl",
                                  "",
                                  7,
                                  1,
                                  colSpan=2)

    scriptDialog.AddControlToGrid("LimitGroupLabel", "LabelControl", "Limits",
                                  8, 0, "The Limits that your job requires.",
                                  False)
    scriptDialog.AddControlToGrid("LimitGroupBox", "LimitGroupControl", "", 8, 1, colSpan=2)

    scriptDialog.AddControlToGrid(
        "DependencyLabel", "LabelControl", "Dependencies", 9, 0,
        "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering.",
        False)
    scriptDialog.AddControlToGrid("DependencyBox", "DependencyControl", "", 9, 1, colSpan=2)

    scriptDialog.AddControlToGrid(
        "OnJobCompleteLabel", "LabelControl", "On Job Complete", 10, 0,
        "If desired, you can automatically archive or delete the job when it completes.",
        False)
    scriptDialog.AddControlToGrid("OnJobCompleteBox", "OnJobCompleteControl",
                                  "Nothing", 10, 1)
    scriptDialog.AddSelectionControlToGrid(
        "SubmitSuspendedBox", "CheckBoxControl", False,
        "Submit Job As Suspended", 10, 2,
        "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render."
    )
    scriptDialog.EndGrid()

    ################################################################################

    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid("Separator3","SeparatorControl","FFmpeg Options",0,0,colSpan=2)

    scriptDialog.AddControlToGrid("PassNameLabel", "LabelControl", "Modo Pass Names", 1, 0, "Pass to render. ", False)
    passNameBox = scriptDialog.AddComboControlToGrid("PassNameBox", "ComboControl","", ("none", ), 1, 1, colSpan=1)

    scriptDialog.AddControlToGrid("InputLabel", "LabelControl", "Input File",2, 0, "The input file to process.", False)
    inputBox = scriptDialog.AddSelectionControlToGrid("InputBox","FileBrowserControl","","All Files (*)", 2,1)

    passNameBox.ValueModified.connect(SetInput)

    scriptDialog.AddSelectionControlToGrid(
        "InputReplacePaddingBox", "CheckBoxControl", True,
        "Replace Frame in Input File(s) With Padding (file%04d.ext)", 3, 1,
        "If enabled, the frame number in the file name will be replaced by frame padding before being passed to FFMpeg. \n"
        "This should be enabled if you are passing a sequence of images as input."
    )
    
    
    scriptDialog.AddControlToGrid("OutputLabel", "LabelControl", "Output File", 4, 0, "The output file path.", False)
    scriptDialog.AddSelectionControlToGrid("OutputBox", "FileSaverControl", "", "All Files (*)", 4, 1)
    inputBox.ValueModified.connect(SetOutput)

    scriptDialog.AddControlToGrid("FramesLabel", "LabelControl", "Frame List", 5, 0, "The list of frames to render.", False)
    scriptDialog.AddControlToGrid("FramesListBox", "TextControl", "",5,1,colSpan=3)
    
    scriptDialog.AddControlToGrid("FramesLabel", "LabelControl", "Frame Size", 6, 0, "Size of image (1920x1080).", False)
    scriptDialog.AddControlToGrid("FramesSizeBox", "TextControl", "",6,1,colSpan=3)

    scriptDialog.AddControlToGrid("FormatLabel", "LabelControl", "Format", 7,0, "The video container to use. ", False)
    formatBox = scriptDialog.AddComboControlToGrid("vFormatBox","ComboControl", "MP4", ("MP4", "MKV"), 7, 1)
    formatBox.ValueModified.connect(SetOutput)

    scriptDialog.AddControlToGrid("CodecLabel", "LabelControl", "Codec", 8, 0, "The compression type to use. ", False)
    scriptDialog.AddComboControlToGrid("vCodecBox", "ComboControl", "H.264",("H.264", "H.265"), 8, 1)

    scriptDialog.AddControlToGrid("FrameRateLabel", "LabelControl", "Frame Rate", 9, 0, "The frame rate to use. ", False)
    scriptDialog.AddComboControlToGrid("vFrameRateBox", "ComboControl", "24", ("24", "30"), 9, 1)

    scriptDialog.AddControlToGrid(
        "CRFLabel", "LabelControl", "Constant Rate Factor", 10, 0,
        "The range of the CRF scale is 0-51, where 0 is lossless, 23 is the default, and 51 is worst quality possible. \n"
        "A lower value generally leads to higher quality, and a subjectively sane range is 17-28. \n"
        "Consider 17 or 18 to be visually lossless or nearly so; it should look the same or nearly the same as the input but it isn't technically lossless.",
        False)
    scriptDialog.AddRangeControlToGrid("CRFBox", "RangeControl", 23, 0, 51, 2, 1, 10, 1)

    scriptDialog.AddControlToGrid(
        "PresetLabel", "LabelControl", "Preset", 11, 0,
        "A preset is a collection of options that will provide a certain encoding speed to compression ratio. \n"
        "A slower preset will provide better compression (compression is quality per filesize). \n"
        "This means that, for example, if you target a certain file size or constant bit rate, you will achieve better quality with a slower preset. \n"
        "Similarly, for constant quality encoding, you will simply save bitrate by choosing a slower preset. ",
        False)
    scriptDialog.AddComboControlToGrid("vPresetBox", "ComboControl", "medium",
                                       ("ultrafast", "superfast", "veryfast", 
                                        "faster", "fast", "medium","slow", "slower", "veryslow"), 11, 1)

    scriptDialog.EndGrid()
    scriptDialog.EndTabPage()

    scriptDialog.EndTabControl()

    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid("HSpacer1", 0, 0)
    submitButton = scriptDialog.AddControlToGrid("SubmitButton","ButtonControl","Submit",0,1,expand=False)
    submitButton.ValueModified.connect(SubmitButtonPressed)
    closeButton = scriptDialog.AddControlToGrid("CloseButton","ButtonControl","Close",0,2,expand=False)
    closeButton.ValueModified.connect(scriptDialog.closeEvent)
    scriptDialog.EndGrid()

    #Application Box must be listed before version box or else the application changed event will change the version
    settings = ("CategoryBox", "PoolBox", "SecondaryPoolBox",
                "GroupBox", "PriorityBox", "MachineLimitBox", "IsBlacklistBox",
                "MachineListBox", "LimitGroupBox", "SceneBox", "FramesListBox",
                "ChunkSizeBox", "vFormatBox", "vCodecBox", "vFrameRateBox",
                "CRFBox", "vPresetBox")
    scriptDialog.LoadSettings(GetSettingsFilename(), settings)
    scriptDialog.EnabledStickySaving(settings, GetSettingsFilename())

    #########################################################
    if args:
        # fileSeqs = args[0].split(",")
        # for i in fileSeqs:
        #     print "File....................." + i
        fileSeq = args[0]
        originalInput = args[0]
        userInitials = args[1]
        pluginName = args[2]
        jobSceneName = args[3]
        fileDirectory = args[4]
        frameSize = args[5]
        frameList = args[6]
        projectPhase = args[7]
        passNamesString = args[8]
        passNames = passNamesString.split(",")
        scriptDialog.SetItems("PassNameBox", passNames)
        scriptDialog.SetValue("PassNameBox", passNames[0])
    #########################################################

    scriptDialog.ShowDialog(False)
    PopulateJobDetails()
    SetInput()
    SetOutput()
    


def GetSettingsFilename():
    return Path.Combine(ClientUtils.GetUsersSettingsDirectory(),
                        "FFmpegSettings.ini")


def GetExtension():
    global scriptDialog

    formatExt = scriptDialog.GetValue("vFormatBox")
    if formatExt == "MP4":
        return ".mp4"
    elif formatExt == "MKV":
        return ".mkv"
    else:
        return ""

def PopulateJobDetails(*args):
    scriptDialog.SetValue("NameBox", jobSceneName)
    scriptDialog.SetValue("InputBox", fileSeq)
    scriptDialog.SetValue("ProjectPhaseBox", projectPhase)
    scriptDialog.SetValue("FramesSizeBox", frameSize)
    scriptDialog.SetValue("FramesListBox", frameList)

def SetInput(*args):    
    global scriptDialog
    global originalInput
    print("Running SetInput....")
    passName = scriptDialog.GetValue("PassNameBox")
    if passName:
        # inputFile = scriptDialog.GetValue("InputBox")
        padding_ext = originalInput.split('\\')[-1].split('_')[-1]
        dirpath = os.path.dirname(originalInput)
        filenameWOPadding = FrameUtils.GetFilenameWithoutPadding(originalInput)
        # newInput = Path.Combine(dirpath, Path.GetFileNameWithoutExtension( filenameWOPadding ) + GetExtension())
        newInput = Path.Combine(dirpath, "%s%s_%s" % (Path.GetFileNameWithoutExtension(filenameWOPadding), passName, padding_ext))
        scriptDialog.SetValue("InputBox", newInput)

def SetOutput(*args):
    global scriptDialog
    inputFile = scriptDialog.GetValue("InputBox")
    dirpath = os.path.dirname(inputFile)
    filenameWOPadding = FrameUtils.GetFilenameWithoutPadding(inputFile)
    output = Path.Combine(dirpath, Path.GetFileNameWithoutExtension( filenameWOPadding )[:-1] + GetExtension())
    scriptDialog.SetValue("OutputBox", output)


def addZero(tmp):
    num = 4 - len(tmp)
    newNum = tmp
    for i in range(num):
        newNum = "0" + newNum
    return newNum

def SubmitButtonPressed(*args):
    global scriptDialog

    # Check if input files exist.
    inputFile = scriptDialog.GetValue("InputBox")
    replacePadding = scriptDialog.GetValue("InputReplacePaddingBox")

    if (inputFile == ""):
        scriptDialog.ShowMessageBox("No input file specified", "Error")
        return

    inputFile = scriptDialog.GetValue("InputBox")

    # Check output file.
    outputFile = (scriptDialog.GetValue("OutputBox")).strip()

    if (outputFile == ""):
        scriptDialog.ShowMessageBox("No output file specified", "Error")
        return
    else:
        if (PathUtils.IsPathLocal(outputFile)):
            result = scriptDialog.ShowMessageBox(
                "Output file %s is local, are you sure you want to continue?" %
                outputFile, "Warning", ("Yes", "No"))
            if (result == "No"):
                return

    # Check if a valid frame range has been specified.
    frames = scriptDialog.GetValue("FramesListBox")
    startFrame = ""
    frameLength = ""
    if frames:
        startFrame =frames.split('-')[0]
        endFrame = frames.split('-')[1]
        frameLength = str((int(endFrame) - int(startFrame)) + 1)
        startFramePadded = addZero(startFrame)

    framesize = scriptDialog.GetValue("FramesSizeBox")

    # Get arguments
    videoFormat = (scriptDialog.GetValue("vFormatBox"))

    videoCodec = (scriptDialog.GetValue("vCodecBox"))
    if videoCodec == "H.264":
        videoCodec = "libx264"
    if videoCodec == "H.265":
        videoCodec = "libx265"

    videoFrameRate = (scriptDialog.GetValue("vFrameRateBox")).strip()
    videoCRF = (scriptDialog.GetValue("CRFBox"))
    videoPreset = (scriptDialog.GetValue("vPresetBox")).strip()

    # Submit each scene file separately.
    # Create job info file.
    jobInfoFilename = Path.Combine(ClientUtils.GetDeadlineTempPath(),
                                   "ffmpeg_job_info.job")
    writer = StreamWriter(jobInfoFilename, False, Encoding.Unicode)
    writer.WriteLine("Plugin=FFmpeg")
    writer.WriteLine("Name=%s" % scriptDialog.GetValue("NameBox"))
    writer.WriteLine("Comment=%s" % scriptDialog.GetValue("CommentBox"))
    writer.WriteLine("Pool=%s" % scriptDialog.GetValue("PoolBox"))
    writer.WriteLine("SecondaryPool=%s" %
                     scriptDialog.GetValue("SecondaryPoolBox"))
    writer.WriteLine("Group=%s" % scriptDialog.GetValue("GroupBox"))
    writer.WriteLine("Priority=%s" % scriptDialog.GetValue("PriorityBox"))
    writer.WriteLine("TaskTimeoutMinutes=%s" %
                     scriptDialog.GetValue("TaskTimeoutBox"))
    writer.WriteLine("EnableAutoTimeout=%s" %
                     scriptDialog.GetValue("AutoTimeoutBox"))
    writer.WriteLine("ConcurrentTasks=%s" %
                     scriptDialog.GetValue("ConcurrentTasksBox"))
    writer.WriteLine("LimitConcurrentTasksToNumberOfCpus=%s" %
                     scriptDialog.GetValue("LimitConcurrentTasksBox"))

    writer.WriteLine("MachineLimit=%s" %
                     scriptDialog.GetValue("MachineLimitBox"))
    if (bool(scriptDialog.GetValue("IsBlacklistBox"))):
        writer.WriteLine("Blacklist=%s" %
                         scriptDialog.GetValue("MachineListBox"))
    else:
        writer.WriteLine("Whitelist=%s" %
                         scriptDialog.GetValue("MachineListBox"))

    writer.WriteLine("LimitGroups=%s" % scriptDialog.GetValue("LimitGroupBox"))
    writer.WriteLine("JobDependencies=%s" %
                     scriptDialog.GetValue("DependencyBox"))
    writer.WriteLine("OnJobComplete=%s" %
                     scriptDialog.GetValue("OnJobCompleteBox"))

    if (bool(scriptDialog.GetValue("SubmitSuspendedBox"))):
        writer.WriteLine("InitialStatus=Suspended")

    writer.WriteLine("Frames=0")  #%s" % frames )
    writer.WriteLine(
        "ChunkSize=1")  #%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    writer.WriteLine("OutputFilename0=%s" % outputFile)

    writer.Close()

    # Create plugin info file.
    pluginInfoFilename = Path.Combine(ClientUtils.GetDeadlineTempPath(), "ffmpeg_plugin_info.job")
    writer = StreamWriter(pluginInfoFilename, False, Encoding.Unicode)

    writer.WriteLine("InputFile=%s" % inputFile)
    writer.WriteLine("ReplacePadding=%s" % replacePadding)
    writer.WriteLine("OutputFile=%s" % outputFile)
    writer.WriteLine("StartFrame=%s" % startFramePadded)
    writer.WriteLine("FrameLength=%s" % frameLength)
    writer.WriteLine("FrameSize=%s" % framesize)
    writer.WriteLine("VideoFormat=%s" % videoFormat)
    writer.WriteLine("VideoCodec=%s" % videoCodec)
    writer.WriteLine("VideoFrameRate=%s" % videoFrameRate)
    writer.WriteLine("VideoCRF=%s" % str(videoCRF))
    writer.WriteLine("VideoPreset=%s" % videoPreset)

    writer.Close()

    # Setup the command line arguments.
    arguments = StringCollection()

    arguments.Add(jobInfoFilename)
    arguments.Add(pluginInfoFilename)

    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput(arguments)
    scriptDialog.ShowMessageBox(results, "Submission Results")
    # Close the submission dialog
    scriptDialog.CloseDialog()
