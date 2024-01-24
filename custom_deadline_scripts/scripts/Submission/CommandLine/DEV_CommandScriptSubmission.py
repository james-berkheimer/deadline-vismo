import clr

from System.Collections.Specialized import *
from System.IO import *
from System.Text import *
from System.IO import File

from Deadline.Scripting import *

from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
settings = None
count = 0

########################################################################
## Main Function Called By Deadline
########################################################################
def __main__():
    global scriptDialog
    global settings
    global CommandBox
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetTitle( "Submit Command Script Job To Deadline" )
    scriptDialog.SetIcon( Path.Combine( RepositoryUtils.GetRootDirectory(), "plugins/CommandScript/CommandScript.ico" ) )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Job Description", 0, 0, colSpan=2)

    scriptDialog.AddControlToGrid( "NameLabel", "LabelControl", "Job Name", 1, 0, "The name of your job. This is optional, and if left blank, it will default to 'Untitled'.", False )
    scriptDialog.AddControlToGrid( "NameBox", "TextControl", "Untitled", 1, 1 )

    scriptDialog.AddControlToGrid( "CommentLabel", "LabelControl", "Comment", 2, 0, "A simple description of your job. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "CommentBox", "TextControl", "", 2, 1 )

    scriptDialog.AddControlToGrid( "DepartmentLabel", "LabelControl", "Department", 3, 0, "The department you belong to. This is optional and can be left blank.", False )
    scriptDialog.AddControlToGrid( "DepartmentBox", "TextControl", "", 3, 1 )
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
    scriptDialog.AddSelectionControlToGrid( "AutoTimeoutBox", "CheckBoxControl", False, "Enable Auto Task Timeout", 5, 2, "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job. " )

    scriptDialog.AddControlToGrid( "ConcurrentTasksLabel", "LabelControl", "Concurrent Tasks", 6, 0, "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs.", False )
    scriptDialog.AddRangeControlToGrid( "ConcurrentTasksBox", "RangeControl", 1, 1, 16, 0, 1, 6, 1 )
    scriptDialog.AddSelectionControlToGrid( "LimitConcurrentTasksBox", "CheckBoxControl", True, "Limit Tasks To Slave's Task Limit", 6, 2, "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )

    scriptDialog.AddControlToGrid( "MachineLimitLabel", "LabelControl", "Machine Limit", 7, 0, "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit.", False )
    scriptDialog.AddRangeControlToGrid( "MachineLimitBox", "RangeControl", 0, 0, 1000000, 0, 1, 7, 1 )
    scriptDialog.AddSelectionControlToGrid( "IsBlacklistBox", "CheckBoxControl", False, "Machine List Is A Blacklist", 7, 2, "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )

    scriptDialog.AddControlToGrid( "MachineListLabel", "LabelControl", "Machine List", 8, 0, "The whitelisted or blacklisted list of machines.", False )
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
    scriptDialog.AddControlToGrid( "Separator3", "SeparatorControl", "Command Script Options", 0, 0, colSpan=6 )

    scriptDialog.AddControlToGrid("CommandsLabel","LabelControl","Commands to Execute: 0", 1, 0, "Specify a list of commands to execute, one commmand per line.", colSpan=6)
    
    InsertFileButton = scriptDialog.AddControlToGrid("InsertFileButton","ButtonControl","Insert File Path", 2, 0, "Insert a file path at the current cursor location.", False)
    InsertFileButton.ValueModified.connect(InsertFilePressed)
    
    InsertFolderButton = scriptDialog.AddControlToGrid("InsertFolderButton","ButtonControl","Insert Folder Path", 2, 1, "Insert a folder path at the current cursor location.", False)
    InsertFolderButton.ValueModified.connect(InsertFolderPressed)
    
    scriptDialog.AddHorizontalSpacerToGrid("HSpacer1", 2, 2 )
    
    LoadButton = scriptDialog.AddControlToGrid("LoadButton","ButtonControl","Load", row=2, column=3, tooltip="Load a list of commands from a file.", expand=False )
    LoadButton.ValueModified.connect(LoadPressed)
    
    SaveButton = scriptDialog.AddControlToGrid("SaveButton","ButtonControl","Save", row=2, column=4, tooltip="Save the current list of commands to a file.", expand=False )
    SaveButton.ValueModified.connect(SavePressed)
    
    ClearButton=scriptDialog.AddControlToGrid("ClearButton","ButtonControl","Clear", row=2, column=5, tooltip="Clear the current list of commands.", expand=False)
    ClearButton.ValueModified.connect(ClearPressed)
    scriptDialog.EndGrid()
    scriptDialog.AddGrid()
    CommandBox=scriptDialog.AddControlToGrid("CommandsBox","MultiLineTextControl","", 0, 0, colSpan=3)
    CommandBox.ValueModified.connect(CommandsChanged)

    scriptDialog.AddControlToGrid("StartupLabel","LabelControl","Startup Directory",1, 0, "The directory where each command will startup (optional).", False)
    scriptDialog.AddSelectionControlToGrid("StartupBox","FolderBrowserControl","","",1, 1, colSpan=2)

    scriptDialog.AddControlToGrid( "ChunkSizeLabel", "LabelControl", "Commands Per Task", 2, 0, "This is the number of commands that will be rendered at a time for each job task.", False )
    scriptDialog.AddRangeControlToGrid( "ChunkSizeBox", "RangeControl", 1, 1, 1000000, 0, 1, 2, 1, expand=False)
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddHorizontalSpacerToGrid( "HSpacer2", 0, 0 )

    submitButton = scriptDialog.AddControlToGrid( "SubmitButton", "ButtonControl", "Submit", 0, 1, expand=False )
    submitButton.ValueModified.connect(SubmitButtonPressed)

    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 0, 2, expand=False )
    closeButton.ValueModified.connect(scriptDialog.closeEvent)

    scriptDialog.EndGrid()
    
###################################################################################################################################    
###################################################################################################################################    
    
    #Application Box must be listed before version box or else the application changed event will change the version
    settings = ("DepartmentBox","CategoryBox","PoolBox","SecondaryPoolBox","GroupBox","PriorityBox","MachineLimitBox","IsBlacklistBox","MachineListBox","LimitGroupBox","ChunkSizeBox","StartupBox")
    scriptDialog.LoadSettings( GetSettingsFilename(), settings )
    scriptDialog.EnabledStickySaving( settings, GetSettingsFilename() )
    
    scriptDialog.ShowDialog(True)
    
def CommandsChanged(self):
    global count
    count = 0
    #commands = scriptDialog.GetValue("CommandsBox")
    
    #for line in commands.split("\r\n"):
    #for line in commands.replace( "\r", "" ).split( "\n" ):
    for line in scriptDialog.GetItems("CommandsBox"):
        if(len(line)>0):
            count+=1
        else:
            #This is since we can't have blank lines between commands
            break
            
    scriptDialog.SetValue("CommandsLabel","Commands to Execute: " + str(count))

def InsertFilePressed(self):
    global scriptDialog
    
    selection = scriptDialog.ShowOpenFileBrowser( "", "All Files (*)" )
    if selection != None:
        selection = ("\"%s\"" % selection)
        CommandBox.insertPlainText(selection)
        
def InsertFolderPressed(self):
    global scriptDialog
    
    selection = scriptDialog.ShowFolderBrowser( "" )
    if selection != None:
        selection = ("\"%s\"" % selection)
        CommandBox.insertPlainText(selection)
        
def LoadPressed(self):
    global scriptDialog
    
    selection = scriptDialog.ShowOpenFileBrowser( "", "All Files (*)" )
    if selection != None:
        file = open( selection, "r" )
        
        #This gets rid of square charachters in the text box
        #text = file.read().replace( "\n", "\r\n" )
        #scriptDialog.SetValue( "CommandsBox", text )
        text = file.read().replace( "\r\n", "\n" )
        scriptDialog.SetItems( "CommandsBox", tuple(text.split( "\n" )) )
        
        file.close()
    
def SavePressed(self):
    global scriptDialog
    
    #text = scriptDialog.GetValue("CommandsBox")
    
    selection = scriptDialog.ShowSaveFileBrowser( "", "All Files (*)" )
    if selection != None:
        file = open( selection, "w" )
        
        #for line in text.replace( "\r", "" ).split( "\n" ):
        for line in scriptDialog.GetItems("CommandsBox"):
            if len( line ) > 0:
                file.write( line + "\n" )
            else:
                #This is since we can't have blank lines between commands
                break
        
        file.close()
    
def ClearPressed(self):
    global scriptDialog
    scriptDialog.SetValue("CommandsBox","")
    
def GetSettingsFilename():
    return Path.Combine( GetDeadlineSettingsPath(), "CommandScriptSettings.ini" )
    
def SubmitButtonPressed(*args):
    global scriptDialog
    global count
    
    if(count==0):
        scriptDialog.ShowMessageBox("The command list is empty","Error")
        return
        
    startupDir = scriptDialog.GetValue("StartupBox").strip()
    
    #~ if(len(startupDir)==0):
        #~ scriptDialog.ShowMessageBox("No startup directory given.","Error")
        #~ return
        
    #~ try:
        #~ if not Directory.Exists(startupDir):
            #~ scriptDialog.ShowMessageBox("Startup directory " + startupDir + " doesn't exist.","Error")
            #~ return
    #~ except:
        #~ scriptDialog.ShowMessageBox("Startup directory path " + startupDir + " is invalid.","Error")
        #~ return
    
    # Create job info file.
    jobInfoFilename = Path.Combine( GetDeadlineTempPath(), "cmd_job_info.job" )
    writer = StreamWriter( jobInfoFilename, False, Encoding.Unicode )
    writer.WriteLine( "Plugin=CommandScript" )
    writer.WriteLine( "Name=%s" % scriptDialog.GetValue( "NameBox" ) )
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
    
    writer.WriteLine( "Frames=0-" + str(count-1))
    writer.WriteLine( "ChunkSize=%s" % scriptDialog.GetValue( "ChunkSizeBox" ) )
    
    writer.Close()
    
    # Create plugin info file.
    pluginInfoFilename = Path.Combine( GetDeadlineTempPath(), "cmd_plugin_info.job" )
    writer = StreamWriter( pluginInfoFilename, False, Encoding.Unicode )
    
    writer.WriteLine("StartupDirectory="+startupDir)
    writer.Close()
    
    commandsFilename = Path.Combine( GetDeadlineTempPath(), "commandsfile.txt")
    writer = StreamWriter( commandsFilename, False, Encoding.Unicode )
    
    #commands = scriptDialog.GetValue("CommandsBox").split("\r\n")
    #commands = scriptDialog.GetValue("CommandsBox").replace( "\r", "" ).split( "\n" )
    #for i in range(0,count):
    #	writer.WriteLine(commands[i])
    for line in scriptDialog.GetItems("CommandsBox"):
        if len( line ) > 0:
            writer.WriteLine(line)
        else:
            #This is since we can't have blank lines between commands
            break
    writer.Close()
    
    # Setup the command line arguments.
    arguments = StringCollection()
    
    arguments.Add( jobInfoFilename )
    arguments.Add( pluginInfoFilename )
    arguments.Add( commandsFilename )
    
    # Now submit the job.
    results = ClientUtils.ExecuteCommandAndGetOutput( arguments )
    scriptDialog.ShowMessageBox( results, "Submission Results" )
