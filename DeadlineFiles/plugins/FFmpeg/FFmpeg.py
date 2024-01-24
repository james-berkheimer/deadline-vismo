from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *


def GetDeadlinePlugin():
    return FFmpegPlugin()


def CleanupDeadlinePlugin(deadlinePlugin):
    deadlinePlugin.Cleanup()


class FFmpegPlugin(DeadlinePlugin):
    def __init__(self):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks

    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback

        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback

    def InitializeProcess(self):
        self.SingleFramesOnly = False
        self.StdoutHandling = True

        self.AddStdoutHandlerCallback(
            ".*Error.*").HandleCallback += self.HandleStdoutError

    def RenderExecutable(self):
        FFmpegExeList = self.GetConfigEntry("FFmpeg_RenderExecutable")
        FFmpegExe = FileUtils.SearchFileList(FFmpegExeList)

        if (FFmpegExe == ""):
            self.FailRender(
                "No file found in the semicolon separated list \"" +
                FFmpegExeList +
                "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor."
            )

        return FFmpegExe

    def RenderArgument(self):
        inputFile = self.GetPluginInfoEntryWithDefault("InputFile", "")
        replacePadding = self.GetPluginInfoEntryWithDefault("ReplacePadding", "")

        
        outputFile = self.GetPluginInfoEntryWithDefault("OutputFile", "")
        outputFile = RepositoryUtils.CheckPathMapping(outputFile)
        outputFile = self.ProcessPath(outputFile)

        startFrame = self.GetPluginInfoEntryWithDefault("StartFrame", "")
        frameLength = self.GetPluginInfoEntryWithDefault("FrameLength", "")
        frameSize = self.GetPluginInfoEntryWithDefault("FrameSize", "")
        vFormat = self.GetPluginInfoEntryWithDefault("VideoFormat", "")
        vCodec = self.GetPluginInfoEntryWithDefault("VideoCodec", "")
        frameRate = self.GetPluginInfoEntryWithDefault("VideoFrameRate", "")
        videoCRF = self.GetPluginInfoEntryWithDefault("VideoCRF", "")
        vPreset = self.GetPluginInfoEntryWithDefault("VideoPreset", "")


        if (outputFile == ""):
            self.FailRender("No output file was specified.")

        renderArgument = ""

        if startFrame != "":
            renderArgument += " -start_number \"%s\"" % startFrame
            
        if inputFile != "":
            inputFile = RepositoryUtils.CheckPathMapping(inputFile)
            inputFile = self.ProcessPath(inputFile)

            # img-%04d
            if replacePadding:
                currPadding = FrameUtils.GetFrameStringFromFilename(inputFile)
                paddingSize = len(currPadding)

                if '-' in currPadding:
                    front = "-%"
                    paddingSize = paddingSize - 1
                else:
                    front = "%"

                if paddingSize > 0:
                    padding = front + StringUtils.ToZeroPaddedString(paddingSize, 2, False) + "d"
                    inputFile = FrameUtils.SubstituteFrameNumber(inputFile, padding)

            renderArgument += " -i \"%s\"" % inputFile

        if frameSize != "":
            renderArgument += " -s \"%s\"" % frameSize

        if frameRate != "":
            renderArgument += " -r \"%s\"" % frameRate
            
        if vCodec != "":
            renderArgument += " -c:v \"%s\"" % vCodec
            
        if videoCRF != "":
            renderArgument += " -crf \"%s\"" % videoCRF
            
        if vPreset != "":
            renderArgument += " -preset \"%s\"" % vPreset

        if frameLength != "":
            renderArgument += " -vframes \"%s\"" % frameLength
            
        # -y overwrite output files
        renderArgument += " -y" 
        renderArgument += " \"%s\"" % outputFile

        print("Render Argument")
        print(renderArgument)
        self.LogInfo("Render Argument")
        self.LogInfo(renderArgument)
        return renderArgument

    def ProcessPath(self, filepath):
        if SystemUtils.IsRunningOnWindows():
            filepath = filepath.replace("/", "\\")
            if filepath.startswith("\\") and not filepath.startswith("\\\\"):
                filepath = "\\" + filepath
        else:
            filepath = filepath.replace("\\", "/")
        return filepath

    def PreRenderTasks(self):
        self.LogInfo("FFmpeg job starting...")

    def PostRenderTasks(self):
        self.LogInfo("FFmpeg job finished.")

    def HandleStdoutError(self):
        self.FailRender(self.GetRegexMatch(0))
