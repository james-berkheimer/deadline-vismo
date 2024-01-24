from System.Text.RegularExpressions import *

from Deadline.Plugins import *
from Deadline.Scripting import *

######################################################################
## This is the function that Deadline calls to get an instance of the
## main DeadlinePlugin class.
######################################################################
def GetDeadlinePlugin():
    return CommandLinePlugin()

def CleanupDeadlinePlugin( deadlinePlugin ):
    deadlinePlugin.Cleanup()

######################################################################
## This is the main DeadlinePlugin class for the CommandLine plugin.
######################################################################
class CommandLinePlugin(DeadlinePlugin):
    
    def __init__( self ):
        self.InitializeProcessCallback += self.InitializeProcess
        self.RenderExecutableCallback += self.RenderExecutable
        self.RenderArgumentCallback += self.RenderArgument
    
    def Cleanup(self):
        for stdoutHandler in self.StdoutHandlers:
            del stdoutHandler.HandleCallback
        
        del self.InitializeProcessCallback
        del self.RenderExecutableCallback
        del self.RenderArgumentCallback
    
    def InitializeProcess(self):
        # Set the plugin specific settings.
        self.SingleFramesOnly = False
        
        # Set the process specific settings.
        self.StdoutHandling = True
        self.PopupHandling = True
    
    def RenderExecutable(self):
        return RepositoryUtils.CheckPathMapping(self.GetPluginInfoEntry( "Executable" ).strip())
    
    def RenderArgument(self):
        arguments = RepositoryUtils.CheckPathMapping(self.GetPluginInfoEntry( "Arguments" ).strip())
        return arguments


