import re
import os

from System import *
from System.Diagnostics import *
from System.IO import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return MayaCmdPlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the FusionCmd plugin.
######################################################################
class MayaCmdPlugin (DeadlinePlugin):
    Version = 0
    Build = "none"
    Renderer = "mayasoftware"
    
    TempSceneFilename = ""
    LocalRendering = False
    LocalRenderDirectory = ""
    NetworkRenderDirectory = ""
    RegionRendering = False
    SingleRegionJob = False
    SingleRegionFrame = 0
    SingleRegionIndex = ""
    FinishedFrameCount = 0
    IgnoreError211 = False
    
    PreviousFinishedFrame = ""
    SkipNextFrame = False
    
    vrayRenderingImage = False
    
    CausticCurrentFrame = 0
    CausticTotalPasses = 0
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
        self.PreRenderTasksCallback += self.PreRenderTasks
        self.PostRenderTasksCallback += self.PostRenderTasks
        self.CheckExitCodeCallback += self.CheckExitCode

        self.initialFrame = None
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
        del self.PreRenderTasksCallback
        del self.PostRenderTasksCallback
        del self.CheckExitCodeCallback
    
    ## Called by Deadline to initialize the process.
    def InitializeProcess( self ):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        self.PluginType = PluginType.Simple

        # Set the process specific settings.
        self.ProcessPriority = ProcessPriorityClass.BelowNormal
        self.UseProcessTree = True
        self.PopupHandling = True
        self.StdoutHandling = True

        # FumeFX initial values to support Task Render Status
        self.FumeFXStartFrame = 0
        self.FumeFXEndFrame = 0
        self.FumeFXCurrFrame = 0
        self.FumeFXMemUsed = "0Mb"
        self.FumeFXFrameTime = "00:00.00"
        self.FumeFXEstTime = "00:00:00"

        # FumeFX STDout Handlers (requires min. FumeFX v3.5.3)
        self.AddStdoutHandlerCallback( ".*FumeFX: Starting simulation \(([-]?[0-9]+) - ([-]?[0-9]+)\).*" ).HandleCallback += self.HandleFumeFXProgress # 0: STDOUT: "FumeFX: Starting simulation (-20 - 40)."
        self.AddStdoutHandlerCallback( ".*FumeFX: Frame: ([-]?[0-9]+)" ).HandleCallback += self.HandleFumeFXProgress # 0: STDOUT: "FumeFX: Frame: -15"
        self.AddStdoutHandlerCallback( ".*FumeFX: Memory used: ([0-9]+[a-zA-Z]*)" ).HandleCallback += self.HandleFumeFXProgress # 0: STDOUT: "FumeFX: Memory used: 86Mb"
        self.AddStdoutHandlerCallback( ".*FumeFX: Frame Time: ([0-9]+:[0-9]+\.[0-9]+)" ).HandleCallback += self.HandleFumeFXProgress # 0: STDOUT: "FumeFX: Frame Time: 00:01.69"
        self.AddStdoutHandlerCallback( ".*FumeFX: Estimated Time: ([0-9]+:[0-9]+:[0-9]+)" ).HandleCallback += self.HandleFumeFXProgress # 0: STDOUT: "FumeFX: Estimated Time: 00:00:18"

        self.Renderer = self.GetPluginInfoEntryWithDefault( "Renderer", "mayaSoftware" ).lower()
        
        # Catch licensing errors.
        self.AddStdoutHandlerCallback( "FLEXlm error: .*").HandleCallback += self.HandleFatalError
        self.AddStdoutHandlerCallback( "Maya: License was not obtained").HandleCallback += self.HandleFatalError
        
        # Was there something wrong in the command line?
        self.AddStdoutHandlerCallback( "Usage: Render .*" ).HandleCallback += self.HandleUsageError 
        
        # Progress updates, works when rendering multiple frames per chunk.
        self.AddStdoutHandlerCallback( "Finished Rendering.*\\.([0-9]+)\\.[^\\.]+" ).HandleCallback += self.HandleChunkedProgress1 
        self.AddStdoutHandlerCallback( ".*Finished Rendering.*" ).HandleCallback += self.HandleChunkedProgress2

        # CUDA errors piped as stdout.
        self.AddStdoutHandlerCallback( ".*CUDA_ERROR_UNKNOWN.*" ).HandleCallback += self.HandleFatalError
        self.AddStdoutHandlerCallback( ".*Failed to init the CUDA driver API.*" ).HandleCallback += self.HandleFatalError
        self.AddStdoutHandlerCallback( ".*The system does not support the required CUDA compute capabilities.*" ).HandleCallback += self.HandleFatalError
        
        # Some status messages.
        self.AddStdoutHandlerCallback( "Constructing shading groups|Rendering current frame" ).HandleCallback += self.HandleStatusMessage 
        
        # Error message handling.
        self.AddStdoutHandlerCallback( ".*Error: .*|.*Warning: .*" ).HandleCallback += self.HandleErrorMessage 
        
        # Mental Ray progress handling.
        self.AddStdoutHandlerCallback( "progr: +([0-9]+\\.[0-9]+)% +rendered" ).HandleCallback += self.HandleMentalRayProgress 
        self.AddStdoutHandlerCallback( "progr: +([0-9]+\\.[0-9]+)% +computing final gather points" ).HandleCallback += self.HandleMentalRayGathering 
        self.AddStdoutHandlerCallback( "progr: writing image file .* \\(frame ([0-9]+)\\)" ).HandleCallback += self.HandleMentalRayWritingFrame 
        self.AddStdoutHandlerCallback( "progr: +rendering finished" ).HandleCallback += self.HandleMentalRayComplete 
        
        self.AddStdoutHandlerCallback( "\\| render done" ).HandleCallback += self.HandleProgressMessage2 
        self.AddStdoutHandlerCallback( "\\[PROGRESS\\] Completed frame*" ).HandleCallback += self.HandleProgressMessage2 
        self.AddStdoutHandlerCallback( ".*\\[PROGRESS\\] TURTLE rendering frame 100\\.00.*" ).HandleCallback += self.HandleProgressMessage2 
        self.AddStdoutHandlerCallback( ".*Render complete.*" ).HandleCallback += self.HandleProgressMessage2 
        
        self.AddStdoutHandlerCallback( "\\[PROGRESS\\] Percentage of rendering done: (.*)" ).HandleCallback += self.HandleProgressMessage3 
        self.AddStdoutHandlerCallback( ".*\\[PROGRESS\\] TURTLE rendering frame ([0-9]+\\.[0-9]+).*" ).HandleCallback += self.HandleProgressMessage3 
        self.AddStdoutHandlerCallback( ".*RIMG : +([0-9]+)%" ).HandleCallback += self.HandleProgressMessage3 
        #self.AddStdoutHandler( "([0-9]+)%", self.HandleProgressMessage3 )
        
        if self.Renderer == "vray" or self.Renderer == "vrayexport":
            self.vrayRenderingImage = False
            self.AddStdoutHandlerCallback( "V-Ray error: .*" ).HandleCallback += self.HandleFatalError
            self.AddStdoutHandlerCallback( "V-Ray: Building light cache*" ).HandleCallback += self.HandleVrayMessage 
            self.AddStdoutHandlerCallback( "V-Ray: Prepass ([0-9]+) of ([0-9]+)*" ).HandleCallback += self.HandleVrayMessage 
            self.AddStdoutHandlerCallback( "V-Ray: Rendering image*" ).HandleCallback += self.HandleVrayMessage 
            self.AddStdoutHandlerCallback( "V-Ray: +([0-9]+)%" ).HandleCallback += self.HandleVrayProgress 
            self.AddStdoutHandlerCallback( "V-Ray: +([0-9]+) %" ).HandleCallback += self.HandleVrayProgress 
            self.AddStdoutHandlerCallback( "([0-9]+) % completed" ).HandleCallback += self.HandleVrayProgress 
            self.AddStdoutHandlerCallback( "V-Ray: Total frame time" ).HandleCallback += self.HandleVrayFrameComplete 
            
            self.AddStdoutHandlerCallback( "V-Ray: Updating frame at time ([0-9]+)" ).HandleCallback += self.HandleVrayExportProgress 
            self.AddStdoutHandlerCallback( "V-Ray: Render complete" ).HandleCallback += self.HandleVrayExportComplete 
        
        if self.Renderer == "renderman" or self.Renderer == "rendermanris" or self.Renderer == "rendermanexport":
            self.AddStdoutHandlerCallback( "rfm Notice: Rendering .* at ([0-9]+)" ).HandleCallback += self.HandleRendermanProgress 
        
        # Catch 3Delight Errors
        if self.Renderer == "3delight":
            self.AddStdoutHandlerCallback( ".*3DL ERROR .*" ).HandleCallback += self.HandleFatalError
            self.AddStdoutHandlerCallback( r"\[\d+\.?\d* \d+\.?\d* \d+\.?\d*\]" ).HandleCallback += self.HandlePointCloudOutput
        
        # Catch Arnold Errors
        if self.Renderer == "arnold" or self.Renderer == "arnoldexport":
            self.AddStdoutHandlerCallback( r"Plug-in, \"mtoa\", was not found on MAYA_PLUG_IN_PATH" ).HandleCallback += self.HandleFatalError
            self.AddStdoutHandlerCallback( r"\[mtoa\] Failed batch render" ).HandleCallback += self.HandleFatalError
        
        if self.Renderer == "octanerender":
            self.AddStdoutHandlerCallback( r"Octane: starting animation of frame" ).HandleCallback += self.HandleOctaneStartFrame
            self.AddStdoutHandlerCallback( r"Octane: Refreshed image, ([0-9]+) samples per pixel of ([0-9]+)" ).HandleCallback += self.HandleOctaneProgress
        
        if self.Renderer == "causticvisualizer":
            self.AddStdoutHandlerCallback( r"Executing frame ([0-9]+)" ).HandleCallback += self.HandleCausticVisualizerCurrentFrame
            self.AddStdoutHandlerCallback( r"Rendering ([0-9]+) passes" ).HandleCallback += self.HandleCausticVisualizerTotalPasses
            self.AddStdoutHandlerCallback( r"Rendered to pass ([0-9]+)" ).HandleCallback += self.HandleCausticVisualizerCurrentPass
        
        if self.Renderer == "redshift":
            self.AddStdoutHandlerCallback( r"Frame rendering aborted." ).HandleCallback += self.HandleFatalError
            self.AddStdoutHandlerCallback( r"Rendering was internally aborted" ).HandleCallback += self.HandleFatalError
            self.AddStdoutHandlerCallback( r'Cannot find procedure "rsPreference"' ).HandleCallback += self.HandleFatalError
        
        self.AddStdoutHandlerCallback( "\\[PROGRESS\\] ([0-9]+) percent" ).HandleCallback += self.HandleProgressMessage1 
        self.AddStdoutHandlerCallback( "([0-9]+)%" ).HandleCallback += self.HandleProgressMessage1 
        
        # Set the popup ignorers.
        self.AddPopupIgnorer( ".*entry point.*" )
        self.AddPopupIgnorer( ".*Entry Point.*" )
        
        # Ignore Vray popup
        self.AddPopupIgnorer( ".*Render history settings.*" )
        self.AddPopupIgnorer( ".*Render history note.*" )

        # Handle QuickTime popup dialog
        # "QuickTime does not support the current Display Setting.  Please change it and restart this application."
        self.AddPopupHandler( "Unsupported Display", "OK" )
        self.AddPopupHandler( "Nicht.*", "OK" )
        
    ## Called by Deadline to get the render executable.
    def RenderExecutable( self ):
        self.LogInfo( "Rendering with Maya version " + str(self.Version) )
        
        versionString = str( self.Version ).replace( ".", "_" )
        
        mayaExecutable = ""
        mayaExeList = self.GetConfigEntry( "RenderExecutable" + versionString )
        
        self.Build = self.GetPluginInfoEntryWithDefault( "Build", "None" ).lower()
        
        if(SystemUtils.IsRunningOnWindows()):
            if( self.Build == "32bit"):
                self.LogInfo( "Enforcing 32 bit build of Maya" )
                mayaExecutable = FileUtils.SearchFileListFor32Bit( mayaExeList )
                if( mayaExecutable == "" ):
                    self.LogWarning( "32 bit Maya " + versionString + " render executable was not found in the semicolon separated list \"" + mayaExeList + "\". Checking for any executable that exists instead." )
            
            elif( self.Build == "64bit"):
                self.LogInfo( "Enforcing 64 bit build of Maya" )
                mayaExecutable = FileUtils.SearchFileListFor64Bit( mayaExeList )
                if( mayaExecutable == "" ):
                    self.LogWarning( "64 bit Maya " + versionString + " render executable was not found in the semicolon separated list \"" + mayaExeList + "\". Checking for any executable that exists instead." )
            
        if( mayaExecutable == "" ):
            self.LogInfo( "Not enforcing a build of Maya" )
            mayaExecutable = FileUtils.SearchFileList( mayaExeList )
            if( mayaExecutable == "" ):
                self.FailRender( "Maya " + versionString + " render executable was not found in the semicolon separated list \"" + mayaExeList + "\". The path to the render executable can be configured from the Plugin Configuration in the Deadline Monitor." )
        
        return mayaExecutable
    
    ## Called by Deadline to get the render arguments.
    def RenderArgument( self ):
        self.LocalRendering = self.GetBooleanPluginInfoEntryWithDefault( "LocalRendering", False )
        
        self.NetworkRenderDirectory = self.GetPluginInfoEntryWithDefault( "OutputFilePath", "" ).strip().replace( "\\", "/" )
        self.NetworkRenderDirectory = RepositoryUtils.CheckPathMapping( self.NetworkRenderDirectory ).replace( "\\", "/" )
        if( len( self.NetworkRenderDirectory ) > 0 and ( self.NetworkRenderDirectory.endswith( "\\" ) or self.NetworkRenderDirectory.endswith( "/" ) ) ):
            self.NetworkRenderDirectory = self.NetworkRenderDirectory.rstrip( "/\\" )
        if SystemUtils.IsRunningOnWindows() and self.NetworkRenderDirectory.startswith( "/" ) and not self.NetworkRenderDirectory.startswith( "//" ):
            self.NetworkRenderDirectory = "/" + self.NetworkRenderDirectory
        
        if( self.LocalRendering and self.Renderer != "mentalrayexport" and self.Renderer != "vrayexport" and self.Renderer != "rendermanexport" ):
            if( len( self.NetworkRenderDirectory ) == 0 ):
                self.LocalRendering = False
                self.LogInfo( "OutputFilePath was not specified in the plugin info file, rendering to network drive" )
            else:
                self.LocalRenderDirectory = self.CreateTempDirectory( "mayaOutput" )
                self.LogInfo( "Rendering to local drive, will copy files and folders to final location after render is complete" )
        else:
            self.LogInfo( "Rendering to network drive" )
            self.LocalRendering = False
        
        self.IgnoreError211 = self.GetBooleanPluginInfoEntryWithDefault( "IgnoreError211", False )
        
        rendererArguments = ""
        
        usingRenderLayers = self.GetBooleanPluginInfoEntryWithDefault( "UsingRenderLayers", False )
        renderLayer = self.GetPluginInfoEntryWithDefault( "RenderLayer", "" ).strip()
        
        self.RegionRendering = self.GetBooleanPluginInfoEntryWithDefault( "RegionRendering", False )
        self.SingleRegionJob = self.IsTileJob()
        self.SingleRegionFrame = str(self.GetStartFrame())
        self.SingleRegionIndex = self.GetCurrentTaskId()
        
        # These can be different for some renderers.
        byFrameArg = "-b"
        renLayerArg = "-rl"
        
        # If this is a render layer job, but no layer was specified, then assume that all layers
        # are being rendered as part of the same job.
        if( self.Renderer == "file" or ( usingRenderLayers and len( renderLayer ) == 0 ) ):
            self.LogInfo( "Rendering all layers - using the renderer(s) set in the Maya render settings." )
            
            rendererArguments += " -r file"
            
        else:
            if( self.Renderer == "vray" ):
                self.LogInfo( "Rendering with VRay." )
                
                rendererArguments += " -r vray " + self.GetTileRenderArgument()
                rendererArguments += " -threads " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                
            elif( self.Renderer == "vrayexport" ):
                self.LogInfo( "Exporting with VRay" )
                
                rendererArguments += " -r vray -exportFileName \"" + self.GetPluginInfoEntry( "VRayExportFile" ) + "\" -noRender"
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )

            elif( self.Renderer == "mayakrakatoa" ):
                self.LogInfo( "Exporting with Krakatoa" )
                
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                
            elif( self.Renderer == "maxwell" ):
                self.LogInfo( "Rendering with Maxwell." )
                
                renLayerArg = "-l"
                
                rendererArguments += " -r maxwell "
                rendererArguments += " -nt " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -rt ", self.GetPluginInfoEntryWithDefault( "MaxwellRenderTime", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -sl ", self.GetPluginInfoEntryWithDefault( "MaxwellSamplingLevel", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                
                cmdArguments = ""
                
                slaveFound = False
                thisSlave = self.GetSlaveName().lower()
                interactiveSlaves = self.GetConfigEntryWithDefault( "MaxwellInteractiveSlaves", "" ).split( ',' )
                for slave in interactiveSlaves:
                    if slave.lower().strip() == thisSlave:
                        self.LogInfo( "This slave is in the Maxwell interactive license list - an interactive license for Maxwell will be used instead of a render license" )
                        slaveFound = True
                        break
                if not slaveFound:
                    cmdArguments += " -node"
                
                if self.GetBooleanPluginInfoEntryWithDefault( "MaxwellResumeRender", False ):
                    cmdArguments += " -trytoresume"
                
                if len( cmdArguments ) > 0:
                    rendererArguments += " -cmd \"" + cmdArguments.strip() + "\""
                    
            elif( self.Renderer == "maxwellexport" ):
                self.LogInfo( "Exporting to Maxwell MXS file." )
                renLayerArg = "-l"
                
                mxsFile = self.GetPluginInfoEntryWithDefault( "MaxwellMXSFile", "" )
                
                rendererArguments += " -r maxwell "
                rendererArguments += " -mxs \"" + mxsFile.replace( "\\", "/" ) + "\""
                rendererArguments += " -eo true "
                
            elif( self.Renderer == "arnold" or self.Renderer == "arnoldexport" ):
                self.LogInfo( "Rendering with Arnold." )
                
                rendererArguments += " -r arnold " + self.GetTileRenderArgument()
                
                verbosity = self.GetIntegerPluginInfoEntryWithDefault( "ArnoldVerbose", 1 )
                if verbosity > 2: # verbosity can't be higher than 2
                    verbosity = 2
                rendererArguments += " -ai:lve " + str(verbosity)
                
                if( self.Renderer == "arnold" ):
                    rendererArguments += " -rt 0"
                else:
                    rendererArguments += " -rt 1"
                
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                
            elif( self.Renderer == "redshift" ):
                self.LogInfo( "Rendering with Redshift." )
                rendererArguments += " -r redshift " + self.GetTileRenderArgument()
                
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                
                # If the number of gpus per task is set, then need to calculate the gpus to use.
                gpusPerTask = self.GetIntegerPluginInfoEntryWithDefault( "GPUsPerTask", 0 )
                gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "GPUsSelectDevices", "" )

                if gpusPerTask == 0 and gpusSelectDevices != "":
                    self.LogInfo( "Specific GPUs specified, so the following GPUs will be used by RedShift: " + gpusSelectDevices )
                    rendererArguments += " -gpu {" + gpusSelectDevices + "}"

                elif gpusPerTask > 0:
                    gpuList = []
                    for i in range((self.GetThreadNumber() * gpusPerTask), (self.GetThreadNumber() * gpusPerTask) + gpusPerTask):
                        gpuList.append(str(i))
                    
                    gpus = ",".join(gpuList)
                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by RedShift: " + gpus )
                    rendererArguments += " -gpu {" + gpus + "}"
                    
                elif self.OverrideGpuAffinity():
                    gpuList = []
                    for gpuId in self.GpuAffinity():
                        gpuList.append( str( gpuId ) )
                    
                    gpus = ",".join(gpuList)
                    self.LogInfo( "This slave is overriding its GPU affinity, so the following GPUs will be used by RedShift: " + gpus )
                    rendererArguments += " -gpu {" + gpus + "}"
                
            elif( self.Renderer == "gelato" ):
                self.LogInfo( "Rendering with Gelato." )
                
                rendererArguments += " -r gelato"
                rendererArguments += " -n " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -mb ", self.GetPluginInfoEntryWithDefault( "MotionBlur", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                #rendererArguments += StringUtils.BlankIfEitherIsBlank( " -ard ", self.GetPluginInfoEntryWithDefault( "AspectRatio", "" ) )
            
            elif( self.Renderer == "3delight" ):
                self.LogInfo( "Rendering with 3delight." )
                
                byFrameArg = "-inc"
                renLayerArg = "-lr"
                
                rendererArguments += " -r 3delight " + self.GetTileRenderArgument()
                rendererArguments += " -cpus " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
            
            elif( self.Renderer == "finalrender" ):
                self.LogInfo( "Rendering with Final Render" )
                
                rendererArguments += "-r fr -v 2 " + self.GetTileRenderArgument()
                rendererArguments += " -n " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -mb ", self.GetPluginInfoEntryWithDefault( "MotionBlur", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                #rendererArguments += StringUtils.BlankIfEitherIsBlank( " -ard ", self.GetPluginInfoEntryWithDefault( "AspectRatio", "" ) )
            
            elif( self.Renderer == "renderman" or self.Renderer == "rendermanris" ):
                rendererArguments += " -r renderman"
                
                if self.Renderer == "renderman":
                    self.LogInfo( "Rendering with Renderman for Maya" )
                else:
                    self.LogInfo( "Rendering with Renderman RIS for Maya" )
                    rendererArguments += " -ris"
                
                rendererArguments += " " + self.GetTileRenderArgument()
                #rendererArguments += " -n " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -setAttr motionBlur ", self.GetPluginInfoEntryWithDefault( "MotionBlur", "" ) )
                
                width = self.GetPluginInfoEntryWithDefault( "ImageWidth", "" )
                height = self.GetPluginInfoEntryWithDefault( "ImageHeight", "" )
                if( len( width ) > 0 and len( height ) > 0 ):
                    rendererArguments += " -res " + width + " " + height
            
            elif( self.Renderer == "rendermanexport" ):
                self.LogInfo( "Exporting with Renderman for Maya" )
                
                rendererArguments += " -r rib"
                if self.GetBooleanPluginInfoEntryWithDefault( "RenderWithRis", False ):
                    rendererArguments += " -ris"
                
                #rendererArguments += " -n " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                
                width = self.GetPluginInfoEntryWithDefault( "ImageWidth", "" )
                height = self.GetPluginInfoEntryWithDefault( "ImageHeight", "" )
                if( len( width ) > 0 and len( height ) > 0 ):
                    rendererArguments += " -res " + width + " " + height
                
            elif( self.Renderer == "turtle" ):
                self.LogInfo( "Rendering with Turtle" )
                
                rendererArguments += " -r turtle " + self.GetTileRenderArgument()
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                
            elif( self.Renderer == "mentalray" ):
                self.LogInfo( "Rendering with Mental Ray" )
                
                verbosity = 5
                verbosityString = self.GetPluginInfoEntryWithDefault( "MentalRayVerbose", "Progress Messages" )
                if verbosityString == "No Messages":
                    verbosity = 0
                elif verbosityString == "Fatal Messages Only":
                    verbosity = 1
                elif verbosityString == "Error Messages":
                    verbosity = 2
                elif verbosityString == "Warning Messages":
                    verbosity = 3
                elif verbosityString == "Info Messages":
                    verbosity = 4
                elif verbosityString == "Progress Messages":
                    verbosity = 5
                elif verbosityString == "Detailed Messages (Debug)":
                    verbosity = 6
                
                rendererArguments += "-r mr -v " + str(verbosity) + " " + self.GetTileRenderArgument()
                
                numThreads = self.GetIntegerPluginInfoEntryWithDefault( "MaxProcessors", 0 )
                if numThreads > 0:
                    rendererArguments += " -rt " + str(numThreads)
                else:
                    rendererArguments += " -art"
                
                autoMemoryLimit = self.GetBooleanPluginInfoEntryWithDefault( "AutoMemoryLimit", True )
                if autoMemoryLimit:
                    rendererArguments += " -aml"
                else:
                    memoryLimit = self.GetIntegerPluginInfoEntryWithDefault( "MemoryLimit", 0 )
                    if memoryLimit >= 0:
                        rendererArguments += " -mem " + str(memoryLimit)
                
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                
                if self.Version >= 2014 and self.GetBooleanPluginInfoEntryWithDefault( "SkipExistingFrames", False ):
                    rendererArguments += " -skipExistingFrames true"
                
            elif( self.Renderer == "mentalrayexport" ):
                self.LogInfo( "Exporting with Mental Ray" )
                
                rendererArguments += " -r mi -file \"" + self.GetPluginInfoEntry( "MentalRayExportfile" ) + "\""
                
                binary = self.GetBooleanPluginInfoEntryWithDefault( "MentalRayExportBinary", False )
                rendererArguments += " -binary " + str(binary).lower()
                if not binary:
                    rendererArguments += " -tabstop " + self.GetPluginInfoEntryWithDefault( "MentalRayExportTabStop", "8" )
                
                perFrame = self.GetIntegerPluginInfoEntryWithDefault( "MentalRayExportPerFrame", 2 )
                rendererArguments += " -perframe " + str(perFrame)
                if perFrame != 0:
                    rendererArguments += " -padframe " + self.GetPluginInfoEntryWithDefault( "MentalRayExportPadFrame", "4" )
                
                if self.GetBooleanPluginInfoEntryWithDefault( "MentalRayExportPerLayer", False ):
                    rendererArguments += " -perlayer 1"
                else:
                    rendererArguments += " -perlayer 0"
                
                pathnames = self.GetPluginInfoEntryWithDefault( "MentalRayExportPathNames", "" ).strip()
                if len( pathnames ) > 0:
                    pathnames = pathnames.replace( "1", "a" ) # absolute
                    pathnames = pathnames.replace( "2", "r" ) # relative
                    pathnames = pathnames.replace( "3", "n" ) # none
                    rendererArguments += " -exportPathNames " + pathnames
                    
                fragment = self.GetBooleanPluginInfoEntryWithDefault( "MentalRayExportFragment", False )
                if fragment:
                    rendererArguments += " -fragmentExport"
                    
                    materials = self.GetBooleanPluginInfoEntryWithDefault( "MentalRayExportFragmentMaterials", False )
                    if materials:
                        rendererArguments += " -fragmentMaterials"
                    
                    shaders = self.GetBooleanPluginInfoEntryWithDefault( "MentalRayExportFragmentShaders", False )
                    if shaders:
                        rendererArguments += " -fragmentIncomingShdrs"
                    
                    childDag = self.GetBooleanPluginInfoEntryWithDefault( "MentalRayExportFragmentChildDag", False )
                    if childDag:
                        rendererArguments += " -fragmentChildDag"
                    
                filters = self.GetPluginInfoEntryWithDefault( "MentalRayExportFilterString", "" ).strip()
                if len( filters ) > 0:
                    rendererArguments += " -exportFilterString \"" + filters + "\""
    
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                
            elif( self.Renderer == "mayahardware" or self.Renderer == "mayahardware2" ):
                if self.Renderer == "mayahardware":
                    self.LogInfo( "Rendering with Maya Hardware" )
                    rendererArguments += " -r hw"
                else:
                    self.LogInfo( "Rendering with Maya Hardware 2" )
                    rendererArguments += " -r hw2"
                    
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -mb ", self.GetPluginInfoEntryWithDefault( "MotionBlur", "" ) )
                
                if self.GetBooleanPluginInfoEntryWithDefault( "SkipExistingFrames", False ):
                    rendererArguments += " -skipExistingFrames true"
                
            elif( self.Renderer == "mayavector" ):
                self.LogInfo( "Rendering with Maya Vector" )
                
                rendererArguments += " -r vr"
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                
                if self.GetBooleanPluginInfoEntryWithDefault( "SkipExistingFrames", False ):
                    rendererArguments += " -skipExistingFrames true"
                
            elif( self.Renderer == "mayasoftware" ):
                self.LogInfo( "Rendering with Maya Software" )
                
                antialiasing = self.GetPluginInfoEntryWithDefault( "AntiAliasing", "" )
                if antialiasing == "low":
                    antialiasing = "3"
                elif antialiasing == "medium":
                    antialiasing = "2"
                elif antialiasing == "high":
                    antialiasing = "1"
                elif antialiasing == "highest":
                    antialiasing = "0"
                
                rendererArguments += " -r sw " + self.GetTileRenderArgument()
                rendererArguments += " -n " + self.GetPluginInfoEntryWithDefault( "MaxProcessors", "0" )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -eaa ", antialiasing )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -mb ", self.GetPluginInfoEntryWithDefault( "MotionBlur", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )
                
                if self.GetBooleanPluginInfoEntryWithDefault( "SkipExistingFrames", False ):
                    rendererArguments += " -skipExistingFrames true"
                
            elif( self.Renderer == "octanerender" ):
                self.LogInfo( "Rendering with Octane" )
             
                rendererArguments += "-r octane -v true"
                
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -smp ", self.GetPluginInfoEntryWithDefault( "OctaneMaxSamples", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )

                # If the number of gpus per task is set, then need to calculate the gpus to use.
                gpusPerTask = self.GetIntegerPluginInfoEntryWithDefault( "GPUsPerTask", 0 )
                gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "GPUsSelectDevices", "" )
                
                if self.OverrideGpuAffinity():
                    overrideGPUs = self.GpuAffinity()
                    resultGPUs = []
                    
                    if gpusPerTask == 0 and gpusSelectDevices != "":
                        gpus = gpusSelectDevices.split(",")
                        notFoundGPUs = []
                        
                        for gpu in gpus:
                            if int(gpu) in overrideGPUs:
                                resultGPUs.append( gpu )
                            else:
                                notFoundGPUs.append( gpu )
                        
                        if len( notFoundGPUs ) > 0:
                            self.LogWarning( "The slave is overriding its GPU affinity and the following GPUs do not match the slaves affinity so they will not be used: "+ ",".join(notFoundGPUs) )
                        
                        if len( resultGPUs ) == 0:
                            self.FailRender( "The slave does not have affinity for any of the GPUs specified in the job." )      
                    
                    elif gpusPerTask > 0:
                        if gpusPerTask > len( overrideGPUs ):
                            self.LogWarning( "The slave is overriding its GPU affinity and the slave only has affinity for "+str( len( overrideGPUs ) ) + " slaves of the " + str( gpusPerTask ) + " requested." )
                            resultGPUs =  overrideGPUs
                        else:
                            resultGPUs = list( overrideGPUs )[ :gpusPerTask ]
                    else:
                        resultGPUs = overrideGPUs
                    
                    gpuList = []
                    for gpuId in resultGPUs:
                        if int( gpuId ) <8:
                            gpuList.append( gpuId )
                            enabledGpu = int( gpuId ) + 1
                            rendererArguments += " -gpu" + str( enabledGpu )+" 1"

                    # Need to explicitly disable any GPUs not being used
                    for i in range( 0, 8 ):
                        if str( i ) not in resultGPUs:
                            disabledGpu = i + 1
                            rendererArguments += " -gpu" + str( disabledGpu )+" 0"

                elif gpusPerTask == 0 and gpusSelectDevices != "":
                    gpuIds = gpusSelectDevices.split( "," )
                    
                    for gpuId in gpuIds:
                        if int( gpuId ) <8:
                            intGpu = int( gpuId ) + 1
                            rendererArguments += " -gpu" + str( enabledGpu )+" 1"
                    
                    for i in range( 0, 8 ):
                        if str( i ) not in gpuIds: 
                            disabledGpu = i + 1
                            rendererArguments += " -gpu" + str( disabledGpu )+" 0"

                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by Octane: " + gpusSelectDevices )

                elif gpusPerTask > 0:
                    gpuList = []

                    for i in range( ( self.GetThreadNumber() * gpusPerTask ), ( self.GetThreadNumber() * gpusPerTask ) + gpusPerTask ):
                        if int( i ) <8:
                            enabledGpu = i + 1
                            rendererArguments += " -gpu" + str( enabledGpu )+" 1"
                            gpuList.append( str( i ) )

                    for i in range( gpusPerTask + 1, 16 ):
                            disabledGpu = i + 1
                            rendererArguments += " -gpu" + str( disabledGpu )+" 0"


                    gpus = ",".join(gpuList)
                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by Octane: " + gpus )
                
            elif( self.Renderer == "causticvisualizer" ):
                self.LogInfo( "Rendering with Caustic Visualizer" )
                
                rendererArguments += "-r CausticVisualizer -cmvl 4"
                
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )

            elif self.Renderer == "ifmirayphotoreal":
                self.LogInfo( "Rendering with IRay" )

                rendererArguments += " -r Iray " + self.GetTileRenderArgument()

                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -x ", self.GetPluginInfoEntryWithDefault( "ImageWidth", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -y ", self.GetPluginInfoEntryWithDefault( "ImageHeight", "" ) )
                rendererArguments += StringUtils.BlankIfEitherIsBlank( " -percentRes ", self.GetPluginInfoEntryWithDefault( "ImageScale", "" ) )

                iRayMaxSamples = self.GetPluginInfoEntryWithDefault( "IRayMaxSamples", "" )
                rendererArguments += " -maxSamples " + iRayMaxSamples

                # If the number of gpus per task is set, then need to calculate the gpus to use.
                gpusPerTask = self.GetIntegerPluginInfoEntryWithDefault( "GPUsPerTask", 0 )
                gpusSelectDevices = self.GetPluginInfoEntryWithDefault( "GPUsSelectDevices", "" )

                if self.GetBooleanPluginInfoEntryWithDefault( "IRayUseCPUs", False ):
                    rendererArguments += " -rOn 0"

                    cpuLoad = self.GetPluginInfoEntryWithDefault( "IRayCPULoad", "" )
                    rendererArguments += " -cl " + cpuLoad

                    self.LogInfo( "Using CPUs for rendering with IRay, the following will be used for the CPU load: " + str( cpuLoad ) )
                else:
                    rendererArguments += " -rOff 0"

                if self.OverrideGpuAffinity():
                    overrideGPUs = self.GpuAffinity()
                    resultGPUs = []
                    
                    if gpusPerTask == 0 and gpusSelectDevices != "":
                        gpus = gpusSelectDevices.split(",")
                        notFoundGPUs = []
                        
                        for gpu in gpus:
                            if int(gpu) in overrideGPUs:
                                resultGPUs.append( gpu )
                            else:
                                notFoundGPUs.append( gpu )
                        
                        if len( notFoundGPUs ) > 0:
                            self.LogWarning( "The slave is overriding its GPU affinity and the following GPUs do not match the slaves affinity so they will not be used: "+ ",".join(notFoundGPUs) )
                        
                        if len( resultGPUs ) == 0:
                            self.FailRender( "The slave does not have affinity for any of the GPUs specified in the job." )      
                    
                    elif gpusPerTask > 0:
                        if gpusPerTask > len( overrideGPUs ):
                            self.LogWarning( "The slave is overriding its GPU affinity and the slave only has affinity for "+str( len( overrideGPUs ) ) + " slaves of the " + str( gpusPerTask ) + " requested." )
                            resultGPUs =  overrideGPUs
                        else:
                            resultGPUs = list( overrideGPUs )[ :gpusPerTask ]
                    else:
                        resultGPUs = overrideGPUs
                    
                    gpuList = []
                    for gpuId in resultGPUs:
                        gpuList.append( gpuId )
                        enabledGpu = int( gpuId ) + 1
                        rendererArguments += " -rOn " + str( enabledGpu )

                    # Need to explicitly disable any GPUs not being used
                    for i in range( 0, 16 ):
                        if str( i ) not in resultGPUs:
                            disabledGpu = i + 1
                            rendererArguments += " -rOff " + str( disabledGpu )

                elif gpusPerTask == 0 and gpusSelectDevices != "":
                    gpuIds = gpusSelectDevices.split( "," )
                    
                    for gpuId in gpuIds:
                        intGpu = int( gpuId ) + 1
                        rendererArguments += " -rOn " + str( intGpu )
                    
                    for i in range( 0, 16 ):
                        if str( i ) not in gpuIds: 
                            disabledGpu = i + 1
                            rendererArguments += " -rOff " + str( disabledGpu )

                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by IRay: " + gpusSelectDevices )

                elif gpusPerTask > 0:
                    gpuList = []

                    for i in range( ( self.GetThreadNumber() * gpusPerTask ), ( self.GetThreadNumber() * gpusPerTask ) + gpusPerTask ):
                        enabledGpu = i + 1
                        rendererArguments += " -rOn " + str( enabledGpu )
                        gpuList.append( str( i ) )

                    for i in range( gpusPerTask + 1, 16 ):
                            disabledGpu = i + 1
                            rendererArguments += " -rOff " + str( disabledGpu )


                    gpus = ",".join(gpuList)
                    self.LogInfo( "GPUs per task is greater than 0, so the following GPUs will be used by IRay: " + gpus )

                if self.GetBooleanPluginInfoEntryWithDefault( "SkipExistingFrames", False ):
                    rendererArguments += " -skipExistingFrames true"

            else:
                self.LogWarning( "Renderer " + self.Renderer + " is currently unsupported, so falling back to generic render arguments" )
                rendererArguments += " -r file"
            
            if len( renderLayer ) > 0:
                rendererArguments += " " + renLayerArg + " " + renderLayer
        
        allowsFrameRenumbering = not ( self.Renderer == "vray" )
        
        # Set the common arguments which are available for all renderers.
        commonArguments = ""
        
        # If not rendering an animation, don't specify the animation parameters so that the output file isn't padded.
        if self.GetBooleanPluginInfoEntryWithDefault( "Animation", True ):
            frameNumberOffset = self.GetIntegerPluginInfoEntryWithDefault( "FrameNumberOffset", 0 )
            
            if self.GetBooleanPluginInfoEntryWithDefault( "RenderHalfFrames", False ):
                self.LogInfo( "Rendering half frames" )
                if allowsFrameRenumbering:
                    commonArguments += " -s " + str(self.GetStartFrame()) + " -e " + str(self.GetEndFrame() + 0.5) + " " + byFrameArg + " 0.5 -rfs " + str((self.GetStartFrame() * 2) + (frameNumberOffset*2))
                else:
                    self.FailRender( "Rendering Half Frames is not supported by this renderer." )
            else:
                if self.RegionRendering and self.SingleRegionJob:
                    commonArguments += " -s " + str(self.SingleRegionFrame) + " -e " + str(self.SingleRegionFrame) + " " + byFrameArg + " 1"
                else:
                    commonArguments += " -s " + str(self.GetStartFrame()) + " -e " + str(self.GetEndFrame()) + " " + byFrameArg + " 1"
                
                if frameNumberOffset != 0:
                    if allowsFrameRenumbering:
                        commonArguments += " -rfs " + str(self.GetStartFrame() + frameNumberOffset)
                    else:
                        self.LogWarning( "Renumbering Frames is not supported by this renderer." )
        
        renderDirectory = self.NetworkRenderDirectory
        if( len( self.LocalRenderDirectory ) > 0 ):
            renderDirectory = self.LocalRenderDirectory
        
        # These output arguments aren't supported by 3delight.
        if( self.Renderer != "3delight" ):
            commonArguments += StringUtils.BlankIfEitherIsBlank( " -rd \"", StringUtils.BlankIfEitherIsBlank( renderDirectory, "\"" ) )
            
            if self.RegionRendering and self.SingleRegionJob:
                outputFilePrefix = self.GetPluginInfoEntryWithDefault( "RegionPrefix" + self.SingleRegionIndex, "" ).replace( "\\", "/" )
            else:
                outputFilePrefix = self.GetPluginInfoEntryWithDefault( "OutputFilePrefix", "" ).strip().replace( "\\", "/" )
            #commonArguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -im \"", outputFilePrefix ), "\"" )
            
        # commonArguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -cam \"", self.GetPluginInfoEntryWithDefault( "Camera", "") ), "\"" )
        
        # The project path
        projectPath = self.GetPluginInfoEntryWithDefault( "ProjectPath", "" ).strip().replace( "\\", "/" )
        projectPath = RepositoryUtils.CheckPathMapping( projectPath ).replace( "\\", "/" )
        if( len( projectPath ) > 0 and ( projectPath.endswith( "\\" ) or projectPath.endswith( "/" ) ) ):
            projectPath = projectPath.rstrip( "/\\" )
        if SystemUtils.IsRunningOnWindows() and projectPath.startswith( "/" ) and not projectPath.startswith( "//" ):
            projectPath = "/" + projectPath
        
        commonArguments += StringUtils.BlankIfEitherIsBlank( StringUtils.BlankIfEitherIsBlank( " -proj \"", projectPath ), "\"" )
        
        # Build the final argument list.
        renderArguments = ""
        
        #sceneFile = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() ).strip().replace( "\\", "/" )
        #sceneFile = RepositoryUtils.CheckPathMapping( sceneFile ).replace( "\\", "/" )
        #sceneFile = PathUtils.ToPlatformIndependentPath( sceneFile )
        sceneFile = self.TempSceneFilename
        
        commandLineOptions = self.GetPluginInfoEntryWithDefault( "CommandLineOptions", "" )
        if self.GetBooleanPluginInfoEntryWithDefault( "UseOnlyCommandLineOptions", False ):
            renderArguments = commandLineOptions + " \"" + sceneFile + "\""
        else:
            renderArguments = rendererArguments + " " + commonArguments + " " + commandLineOptions + " \"" + sceneFile + "\""
        
        return renderArguments
    
    def GetTileRenderArgument( self ):
        tileArgument = ""
        
        if( self.RegionRendering ):
            if self.SingleRegionJob:
                regionLeft = self.GetPluginInfoEntryWithDefault( "RegionLeft" + self.SingleRegionIndex, "0" )
                regionRight = self.GetPluginInfoEntryWithDefault( "RegionRight" + self.SingleRegionIndex, "0" )
                regionTop = self.GetPluginInfoEntryWithDefault( "RegionTop" + self.SingleRegionIndex, "0" )
                regionBottom = self.GetPluginInfoEntryWithDefault( "RegionBottom" + self.SingleRegionIndex, "0" )
            else:
                regionLeft = self.GetPluginInfoEntryWithDefault( "RegionLeft", "0" ).strip()
                regionRight = self.GetPluginInfoEntryWithDefault( "RegionRight", "0" ).strip()
                regionTop = self.GetPluginInfoEntryWithDefault( "RegionTop", "0" ).strip()
                regionBottom = self.GetPluginInfoEntryWithDefault( "RegionBottom", "0" ).strip()

            if( self.Renderer == "renderman" or self.Renderer == "rendermanris" ):
                resx = self.GetIntegerPluginInfoEntryWithDefault( "ImageWidth", 0 )
                resy = self.GetIntegerPluginInfoEntryWithDefault( "ImageHeight", 0 )
                if( resx > 0 and resy > 0 ):
                    regionLeftPercent = float(regionLeft) / float(resx)
                    regionRightPercent = float(regionRight) / float(resx)
                    regionTopPercent = float(regionTop) / float(resy)
                    regionBottomPercent = float(regionBottom) / float(resy)
                    
                    tileArgument = " -crop " + str(regionLeftPercent) + " " + str(regionRightPercent) + " " + str(regionTopPercent) + " " + str(regionBottomPercent)
            elif( self.Renderer == "turtle" ):
                tileArgument = " -region " + str(regionLeft) + " " + str(regionTop) + " " + str(regionRight) + " " + str(regionBottom)
            elif( self.Renderer == "3delight" ):
                resx = self.GetIntegerPluginInfoEntryWithDefault( "ImageWidth", 0 )
                resy = self.GetIntegerPluginInfoEntryWithDefault( "ImageHeight", 0 )
                if( resx > 0 and resy > 0 ):
                    regionLeftPercent = float(regionLeft) / float(resx)
                    regionRightPercent = float(regionRight) / float(resx)
                    regionTopPercent = float(regionTop) / float(resy)
                    regionBottomPercent = float(regionBottom) / float(resy)
                
                tileArgument = " -crop true -crminx " + str(regionLeftPercent) + " -crminy " + str(regionTopPercent) + " -crmaxx " + str(regionRightPercent) + " -crmaxy " + str(regionBottomPercent)
            elif( self.Renderer == "arnold" or self.Renderer == "redshift" ):
                tileArgument = " -reg " + str(regionLeft) + " " + str(regionRight) + " " + str(regionTop) + " " + str(regionBottom)
            
            elif( self.Renderer == "ifmirayphotoreal" ):
                tileArgument = " -window " + str(regionLeft) + " " + str(regionRight) + " " + str(regionTop) + " " + str(regionBottom)
            
            else:
                tileArgument = " -reg " + str(regionLeft) + " " + str(regionRight) + " " + str(regionTop) + " " + str(regionBottom)
        
        return tileArgument
    
    ## Called by Deadline before the render begins.
    def PreRenderTasks( self ):
        self.FinishedFrameCount = 0
        self.PreviousFinishedFrame = ""
        self.SkipNextFrame = False

        self.LogInfo( "Setting MAYA_DEBUG_ENABLE_CRASH_REPORTING environment variable to 0 for this session. Set to 1 if you need Maya debug log" )
        self.SetEnvironmentVariable( "MAYA_DEBUG_ENABLE_CRASH_REPORTING", "0" )
        
        self.LogInfo( "Setting MAYA_DISABLE_CIP (ADSK Customer Involvement Program) environment variable to 1 for this session" )
        self.SetEnvironmentVariable( "MAYA_DISABLE_CIP", "1" )

        self.LogInfo( "Setting MAYA_DISABLE_CER (ADSK Customer Error Reporting) environment variable to 1 for this session" )
        self.SetEnvironmentVariable( "MAYA_DISABLE_CER", "1" )

        self.LogInfo( "Setting MAYA_DISABLE_CLIC_IPM (ADSK In Product Messaging) environment variable to 1 for this session" )
        self.SetEnvironmentVariable( "MAYA_DISABLE_CLIC_IPM", "1" )

        self.LogInfo( "Setting MAYA_OPENCL_IGNORE_DRIVER_VERSION environment variable to 1 for this session" )
        self.SetEnvironmentVariable( "MAYA_OPENCL_IGNORE_DRIVER_VERSION", "1" )

        self.LogInfo( "Setting MAYA_VP2_DEVICE_OVERRIDE environment variable to VirtualDeviceDx11 for this session" )
        self.SetEnvironmentVariable( "MAYA_VP2_DEVICE_OVERRIDE", "VirtualDeviceDx11" )
        
        self.Version = StringUtils.ParseLeadingNumber( self.GetPluginInfoEntry( "Version" ) )
        self.Version = int(self.Version * 10) / 10.0 # we only want one decimal place
        if not str(self.Version).endswith(".5"):
            self.Version = int(self.Version) * 1.0 # If it's not a *.5 version, then we want to ignore the decimal value
        
        if self.Version >= 2016.5:
            useLegacyRenderLayers = int( self.GetBooleanPluginInfoEntryWithDefault( "UseLegacyRenderLayers", False ) )
            self.LogInfo( "Setting MAYA_ENABLE_LEGACY_RENDER_LAYERS environment variable to %d for this session" % useLegacyRenderLayers )
            self.SetEnvironmentVariable( "MAYA_ENABLE_LEGACY_RENDER_LAYERS", str( useLegacyRenderLayers ) )

        # If on the Mac, set some environment variables (these are normally set by MayaENV.sh when running the Maya Terminal).
        if SystemUtils.IsRunningOnMac():
            mayaExecutable = self.RenderExecutable()
            mayaBinFolder = Path.GetDirectoryName( mayaExecutable )
            usrAwComBin = "/usr/aw/COM/bin"
            usrAwComEtc = "/usr/aw/COM/etc"
            
            self.LogInfo( "Adding " + mayaBinFolder + " to PATH environment variable for this session" )
            self.LogInfo( "Adding " + usrAwComBin + " to PATH environment variable for this session" )
            self.LogInfo( "Adding " + usrAwComEtc + " to PATH environment variable for this session" )
            
            path = Environment.GetEnvironmentVariable( "PATH" )
            if path:
                path = mayaBinFolder + ":" + usrAwComBin + ":" + usrAwComEtc + ":" + path
                self.SetEnvironmentVariable( "PATH", path )
            else:
                self.SetEnvironmentVariable( "PATH", mayaBinFolder + ":" + usrAwComBin + ":" + usrAwComEtc )
            
            mayaLocation = Path.GetDirectoryName( mayaBinFolder )
            self.LogInfo( "Setting MAYA_LOCATION environment variable to " + mayaLocation + " for this session" )
            self.SetEnvironmentVariable( "MAYA_LOCATION", mayaLocation )
            
            mayaMacOSFolder = Path.Combine( mayaLocation, "MacOS" )
            self.LogInfo( "Adding " + mayaMacOSFolder + " to DYLD_LIBRARY_PATH environment variable for this session" )
            libraryPath = Environment.GetEnvironmentVariable( "DYLD_LIBRARY_PATH" )
            if libraryPath:
                libraryPath = mayaMacOSFolder + ":" + libraryPath
                self.SetEnvironmentVariable( "DYLD_LIBRARY_PATH", libraryPath )
            else:
                self.SetEnvironmentVariable( "DYLD_LIBRARY_PATH", mayaMacOSFolder )
            
            mayaFrameworksFolder = Path.Combine( mayaLocation, "Frameworks" )
            self.LogInfo( "Adding " + mayaFrameworksFolder + " to DYLD_FRAMEWORK_PATH environment variable for this session" )
            frameworkPath = Environment.GetEnvironmentVariable( "DYLD_FRAMEWORK_PATH" )
            if frameworkPath:
                frameworkPath = mayaFrameworksFolder + ":" + frameworkPath
                self.SetEnvironmentVariable( "DYLD_FRAMEWORK_PATH", frameworkPath )
            else:
                self.SetEnvironmentVariable( "DYLD_FRAMEWORK_PATH", mayaFrameworksFolder )
            
            mayaPythonVersionsFolder = Path.Combine( mayaFrameworksFolder, "Python.framework/Versions" )
            
            pythonVersion = "2.7"
            mayaPythonVersionFolder = Path.Combine( mayaPythonVersionsFolder, pythonVersion )
            if not Directory.Exists( mayaPythonVersionFolder ):
                pythonVersion = "2.6"
                mayaPythonVersionFolder = Path.Combine( mayaPythonVersionsFolder, pythonVersion )
            
            if Directory.Exists( mayaPythonVersionFolder ):
                self.LogInfo( "Setting PYTHONHOME to " + mayaPythonVersionFolder + " for this session" )
                self.SetEnvironmentVariable( "PYTHONHOME", mayaPythonVersionFolder )
        
        elif SystemUtils.IsRunningOnWindows():
            mayaExecutable = self.RenderExecutable()
            mayaBinFolder = Path.GetDirectoryName( mayaExecutable )
            mayaLocation = Path.GetDirectoryName( mayaBinFolder )
            mayaPythonFolder = Path.Combine( mayaLocation, "Python" )
            if Directory.Exists( mayaPythonFolder ):
                self.LogInfo( "Setting PYTHONHOME to " + mayaPythonFolder + " for this session" )
                self.SetEnvironmentVariable( "PYTHONHOME", mayaPythonFolder )
        
        # Do path mapping as necessary.
        sceneFilename = self.GetPluginInfoEntryWithDefault( "SceneFile", self.GetDataFilename() ).strip().replace( "\\", "/" )
        sceneFilename = RepositoryUtils.CheckPathMapping( sceneFilename ).replace( "\\", "/" )
        
        # We can only do path mapping on .ma files (they're ascii files)
        if Path.GetExtension( sceneFilename ).lower() == ".ma" and self.GetBooleanConfigEntryWithDefault( "EnableMaPathMapping", True ):
            self.LogInfo( "Performing path mapping on ma scene file" )
            
            tempSceneDirectory = self.CreateTempDirectory( "thread" + str(self.GetThreadNumber()) )
            tempSceneFileName = Path.GetFileName( sceneFilename )
            self.TempSceneFilename = Path.Combine( tempSceneDirectory, tempSceneFileName )
            
            RepositoryUtils.CheckPathMappingInFileAndReplace( sceneFilename, self.TempSceneFilename, ("\\","/\""), ("/","\\\"") )
            if SystemUtils.IsRunningOnLinux() or SystemUtils.IsRunningOnMac():
                os.chmod( self.TempSceneFilename, os.stat( sceneFilename ).st_mode )
        else:
            self.TempSceneFilename = sceneFilename
        
        self.TempSceneFilename = PathUtils.ToPlatformIndependentPath( self.TempSceneFilename )
    
    ## Called by Deadline after the render finishes.
    def PostRenderTasks( self ):
        self.initialFrame = None

        if( self.LocalRendering and self.Renderer != "3delight" ):
            self.LogInfo( "Moving output files and folders from " + self.LocalRenderDirectory + " to " + self.NetworkRenderDirectory )
            self.VerifyAndMoveDirectory( self.LocalRenderDirectory, self.NetworkRenderDirectory, False, -1 )
        
        if Path.GetExtension( self.TempSceneFilename ).lower() == ".ma" and self.GetBooleanConfigEntryWithDefault( "EnableMaPathMapping", True ):
            File.Delete( self.TempSceneFilename )
    
    ## Called by Deadline to check the exit code from the renderer.
    def CheckExitCode( self, exitCode ):
        if exitCode != 0:
            if exitCode == 206:
                self.FailRender( "Maya could not parse the command line. Two common causes for this are using the wrong project directory, or using a drive root ( i.e. \"c:\\\" ) as the output directory." )
            elif ( exitCode == 211 and self.IgnoreError211 ):
                self.LogInfo( "Renderer reported an error with error code 211. This will be ignored, since the option to ignore it is specified in the Job Properties." );
            else:
                self.FailRender( "Renderer returned non-zero error code %d. Check the renderer's output." % exitCode )
    
    def HandleFatalError( self ):
        self.FailRender( self.GetRegexMatch(0) )
    
    def HandlePointCloudOutput( self ):
        self.SuppressThisLine()
    
    def HandleUsageError( self ):
        self.FailRender( "Bad command line arguments: " + self.RenderArgument() + "\nMaya Error: " + self.GetPreviousStdoutLine() )
    
    def HandleChunkedProgress1( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( 100 * ( int(self.GetRegexMatch(1)) - startFrame + 1 ) / ( endFrame - startFrame + 1 ) )
    
    def HandleChunkedProgress2( self ):
        self.FinishedFrameCount += 1
        
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( ( 100 * self.FinishedFrameCount ) / ( endFrame - startFrame + 1) )
    
    def HandleStatusMessage( self ):
        self.SetStatusMessage( self.GetRegexMatch(0) )
        
    def HandleErrorMessage( self ):
        errorMessage = self.GetRegexMatch(0)
        
        # This message is always fatal, because it means the scene could not be loaded.
        if( errorMessage.find( "Cannot load scene" ) != -1 ):
            self.FailRender( errorMessage )
        
        if( not self.GetBooleanPluginInfoEntryWithDefault( "StrictErrorChecking", True ) ):
            self.LogWarning( "Strict error checking off, ignoring the following error or warning:" )
        else:
            ignoreError = True

            if( errorMessage.find( "could not get a license" ) != -1 ):
                ignoreError = False
            #elif( errorMessage.find( "Error: Cannot find procedure " ) != -1 ):
            # 	ignoreError = False
            elif( errorMessage.find( "This scene does not have any renderable cameras" ) != -1 ):
                ignoreError = False
            elif( ( errorMessage.find( "Error: Camera" ) != -1 ) and ( errorMessage.find( "does not exist" ) != -1 ) ):
                ignoreError = False
            elif( errorMessage.find( "Warning: The post-processing failed while attempting to rename file" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: Failed to open IFF file for reading" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: An exception has occurred, rendering aborted." ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Cannot open project" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Could not open file. :" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error reading file. :" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: Scene was not loaded properly, please check the scene name" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: Graphics card capabilities are insufficient for rendering." ) != -1 ):
                ignoreError = False
            #elif( errorMessage.find( "Error: No object matches name:" ) != -1 ):
            #	ignoreError = False
            elif( ( errorMessage.find( "Error: The attribute " ) != -1 ) and ( errorMessage.find( "was locked in a referenced file, and cannot be unlocked." ) != -1 ) ):
                ignoreError = False
            elif( errorMessage.find( "Not enough storage is available to process this command." ) != -1 ):
                ignoreError = False
            elif( errorMessage.find("Error: (Mayatomr) : mental ray has stopped with errors, see the log" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Warning: (Mayatomr.Scene) : no render camera found, final scene will be incomplete and can't be rendered" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "mental ray: out of memory" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "The specified module could not be found." ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: (Mayatomr.Export) : mental ray startup failed with errors" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Number of arguments on call to preLayerScript does not match number of parameters in procedure definition." ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: rman Fatal:" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "rman Error:" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: There was a fatal error rendering the scene." ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Could not obtain a license" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Could not read V-Ray environment variable" ) != -1 ):
                ignoreError = False
            elif( ( errorMessage.find( "error 101003:" ) != -1 ) and ( errorMessage.find( "can't create file" ) != -1 ) ):
                ignoreError = False
            elif( errorMessage.find( "can't create file (No such file or directory)" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Fatal Error:" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error writing render region to raw image file." ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: OctaneRender is not activated!" ) != -1 ):
                ignoreError = False
            elif( errorMessage.find( "Error: R12001") != -1 ):
                ignoreError = False
            #elif( errorMessage.find( "was not found on MAYA_PLUG_IN_PATH." ) != -1 ):
            #	ignoreError = False
            
            if( ignoreError ):
                # Check if we're suppressing warnings.
                if self.GetBooleanConfigEntryWithDefault( "SuppressWarnings", False ) and errorMessage.find( "Warning:" ) != -1:
                    self.SuppressThisLine()
                else:
                    # Only print this out if we're not suppressing warnings.
                    self.LogWarning( "Strict error checking on, ignoring the following unrecognized error or warning. If it is fatal, please email support@thinkboxsoftware.com with the error message." )
            else:
                self.FailRender( "Strict error checking on, caught the following error or warning.\n" + errorMessage + "\nIf this error message is unavoidable but not fatal, please email support@thinkboxsoftware.com with the error message, and disable the Maya job setting Strict Error Checking." )
    
    def HandleProgressMessage1( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( ( float(self.GetRegexMatch(1)) + self.FinishedFrameCount * 100 ) / ( endFrame - startFrame + 1 ) )
            #self.SuppressThisLine()
    
    def HandleProgressMessage2( self ):
        self.FinishedFrameCount += 1
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( ( self.FinishedFrameCount * 100 ) / ( endFrame - startFrame + 1 ) )
    
    def HandleProgressMessage3( self ):
        self.SetProgress( float(self.GetRegexMatch(1)) )
        #self.SuppressThisLine()
    
    def HandleVrayMessage ( self ):
        progressStatus = None
        errorMessage = self.GetRegexMatch(0)
        if( errorMessage.find( "V-Ray: Building light cache" ) != -1 ):
            progressStatus = 'Building light cache.'
        elif( errorMessage.find( "V-Ray: Building global photon map" ) != -1 ):
            progressStatus = self.GetRegexMatch(0)
        elif( errorMessage.find( "V-Ray: Prepass" ) != -1 ):
            progressStatus = self.GetRegexMatch(0)
        elif( errorMessage.find( "V-Ray: Rendering image" ) != -1 ):
            progressStatus = self.GetRegexMatch(0)
            self.vrayRenderingImage = True
                
        if progressStatus is not None:
            self.SetStatusMessage(progressStatus)
            
    def HandleVrayProgress ( self ):
        if self.vrayRenderingImage == True:
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()
            if( endFrame - startFrame + 1 != 0 ):
                self.SetProgress( ( float(self.GetRegexMatch(1)) + self.FinishedFrameCount * 100 ) / ( endFrame - startFrame + 1 ) )
    
    def HandleVrayFrameComplete( self ):
        if self.vrayRenderingImage == True:
            self.FinishedFrameCount += 1
            self.vrayRenderingImage = False
    
    def HandleVrayExportProgress( self ):
        if( self.Renderer == "vrayexport" ):
            self.FinishedFrameCount += 1
            
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()
            if( endFrame - startFrame + 1 != 0 ):
                self.SetProgress( ( (self.FinishedFrameCount-1) * 100 ) / ( endFrame - startFrame + 1 ) )
        
    def HandleVrayExportComplete( self ):
        if( self.Renderer == "vrayexport" ):
            self.SetProgress( 100 )
    
    def HandleRendermanProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        totalFrames = endFrame - startFrame + 1

        if totalFrames > 1:
            currentFrame = float( self.GetRegexMatch( 1 ) )
            if self.initialFrame is None:
                self.initialFrame = currentFrame
                
            normalizedFrame = currentFrame
            if self.initialFrame > 1:
                normalizedFrame = currentFrame - startFrame + 1

            self.SetProgress( normalizedFrame * 100.0 / totalFrames )

        self.SetStatusMessage( self.GetRegexMatch( 0 ) )
        
    def HandleOctaneStartFrame( self ):
        self.FinishedFrameCount += 1
    
    def HandleOctaneProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            currSamples = float(self.GetRegexMatch(1))
            maxSampes = float(self.GetRegexMatch(2))
            self.SetProgress( ( (( currSamples * 100.0 ) / maxSampes) + (self.FinishedFrameCount-1) * 100 ) / ( endFrame - startFrame + 1 ) )
        
        self.SetStatusMessage( self.GetRegexMatch(0) )
    
    
    def HandleCausticVisualizerCurrentFrame( self ):
        self.CausticCurrentFrame = int(self.GetRegexMatch(1))
        
    def HandleCausticVisualizerTotalPasses( self ):
        self.CausticTotalPasses = int(self.GetRegexMatch(1))
        
    def HandleCausticVisualizerCurrentPass( self ):
        if self.CausticTotalPasses > 0:
            totalFrameCount = self.GetEndFrame() - self.GetStartFrame() + 1
            if totalFrameCount != 0:
                causticCurrentPass = int(self.GetRegexMatch(1))
                currentFrameCount = self.CausticCurrentFrame - self.GetStartFrame()
                self.SetProgress( ( (( causticCurrentPass * 100 ) / self.CausticTotalPasses) + (currentFrameCount * 100) ) / totalFrameCount )
    
    
    ########################################################################
    ## Mental Ray progress handling.
    ########################################################################
    def HandleMentalRayProgress( self ):
        startFrame = self.GetStartFrame()
        endFrame = self.GetEndFrame()
        if( endFrame - startFrame + 1 != 0 ):
            self.SetProgress( ( float(self.GetRegexMatch(1)) + self.FinishedFrameCount * 100 ) / ( endFrame - startFrame + 1 ) )
            self.SetStatusMessage( self.GetRegexMatch(0) )
            #self.SuppressThisLine()
    
    def HandleMentalRayComplete( self ):
        if self.SkipNextFrame:
            self.SkipNextFrame = False
        else:
            self.FinishedFrameCount += 1
            startFrame = self.GetStartFrame()
            endFrame = self.GetEndFrame()
            if( endFrame - startFrame + 1 != 0 ):
                self.SetProgress( ( self.FinishedFrameCount * 100 ) / ( endFrame - startFrame + 1 ) )
    
    def HandleMentalRayGathering( self ):
        self.SetStatusMessage( self.GetRegexMatch(0) )
        #self.SuppressThisLine()
    
    def HandleMentalRayWritingFrame( self ):
        currFinishedFrame = self.GetRegexMatch(1)
        if self.PreviousFinishedFrame == currFinishedFrame:
            self.SkipNextFrame = True
        else:
            self.PreviousFinishedFrame = currFinishedFrame

    def HandleFumeFXProgress( self ):
        if re.match( r"FumeFX: Starting simulation ", self.GetRegexMatch( 0 ) ):
            self.FumeFXStartFrame = self.GetRegexMatch( 1 )
            self.FumeFXEndFrame = self.GetRegexMatch( 2 )
        elif re.match( r"FumeFX: Frame: ", self.GetRegexMatch( 0 ) ):
            self.FumeFXCurrFrame = self.GetRegexMatch( 1 )
            denominator = float(self.FumeFXEndFrame) - float(self.FumeFXStartFrame) + 1.0
            progress = ( ( float(self.FumeFXCurrFrame) - float(self.FumeFXStartFrame) + 1.0 ) / denominator ) * 100.0
            self.SetProgress( progress )
            msg = "FumeFX: (" + str(self.FumeFXCurrFrame) + " to " + str(self.FumeFXEndFrame) + ") - Mem: " + str(self.FumeFXMemUsed) + " - LastTime: " + str(self.FumeFXFrameTime) + " - ETA: " + str(self.FumeFXEstTime)
            self.SetStatusMessage( msg )
        elif re.match( r"FumeFX: Memory used:", self.GetRegexMatch( 0 ) ):
            self.FumeFXMemUsed = self.GetRegexMatch( 1 )
        elif re.match( r"FumeFX: Frame Time:", self.GetRegexMatch( 0 ) ):
            self.FumeFXFrameTime = self.GetRegexMatch( 1 )
        elif re.match( r"FumeFX: Estimated Time:", self.GetRegexMatch( 0 ) ):
            self.FumeFXEstTime = self.GetRegexMatch( 1 )
        else:
            pass