import os, sys, re, traceback, subprocess
import ast
import threading
import time

try:
    import ConfigParser
except:
    print( "Could not load ConfigParser module, sticky settings will not be loaded/saved" )

import nuke, nukescripts

print "------------------------ In DEV_SubmitNukeToDeadline.py ------------------------"

dialog = None
#deadlineCommand = None
nukeScriptPath = None
deadlineHome = None

class DeadlineDialog( nukescripts.PythonPanel ):
    pools = []
    groups = []
    
    shotgunKVPs = {}
    ftrackKVPs = {}
    
    def __init__( self, maximumPriority, pools, secondaryPools, groups ):
        nukescripts.PythonPanel.__init__( self, "Submit To Dev_Deadline 8", "com.thinkboxsoftware.software.deadlinedialog" )

        width = 605
        height = 730 #Nuke v6 or earlier UI height

        if int(nuke.env[ 'NukeVersionMajor' ]) >= 7: #GPU rendering UI
            height += 20
        if int(nuke.env[ 'NukeVersionMajor' ]) >= 9: #Performance Profiler UI
            height += 40

        self.setMinimumSize( width, height ) # width, height

        self.jobTab = nuke.Tab_Knob( "Deadline_JobOptionsTab", "Job Options" )
        self.addKnob( self.jobTab )
        
        ##########################################################################################
        ## Job Description
        ##########################################################################################
        
        # Job Name
        self.jobName = nuke.String_Knob( "Deadline_JobName", "Job Name" )
        self.addKnob( self.jobName )
        self.jobName.setTooltip( "The name of your job. This is optional, and if left blank, it will default to 'Untitled'." )
        self.jobName.setValue( "Untitled" )
        
        # Comment
        self.comment = nuke.String_Knob( "Deadline_Comment", "Comment" )
        self.addKnob( self.comment )
        self.comment.setTooltip( "A simple description of your job. This is optional and can be left blank." )
        self.comment.setValue( "" )
        
        # Department
        self.department = nuke.String_Knob( "Deadline_Department", "Department" )
        self.addKnob( self.department )
        self.department.setTooltip( "The department you belong to. This is optional and can be left blank." )
        self.department.setValue( "" )
        
        # Project Phase
        self.projectPhase = nuke.String_Knob( "Deadline_ProjectPhase", "Project Phase" )
        self.addKnob( self.projectPhase )
        self.projectPhase.setTooltip( "The Phase the project is in. DVLP, ALPHA, BETA, FINAL" )
        self.projectPhase.setValue( "" )
        
        # Frame Size
        self.frameSize = nuke.String_Knob( "Deadline_FrameSize", "Frame Size" )
        self.addKnob( self.frameSize )
        self.frameSize.setTooltip( "The Frame size of the renders." )
        self.frameSize.setValue( "" )
        
        # File Type
        self.fileType = nuke.String_Knob( "Deadline_FileType", "File Type" )
        self.addKnob( self.fileType )
        self.fileType.setTooltip( "The Type of file that is being rendered." )
        self.fileType.setValue( "" )
        
        # Separator
        self.separator1 = nuke.Text_Knob( "Deadline_Separator1", "" )
        self.addKnob( self.separator1 )
        
        ##########################################################################################
        ## Job Scheduling
        ##########################################################################################
        
        # Pool
        self.pool = nuke.Enumeration_Knob( "Deadline_Pool", "Pool", pools )
        self.addKnob( self.pool )
        self.pool.setTooltip( "The pool that your job will be submitted to." )
        self.pool.setValue( "none" )
        
        # Secondary Pool
        self.secondaryPool = nuke.Enumeration_Knob( "Deadline_SecondaryPool", "Secondary Pool", secondaryPools )
        self.addKnob( self.secondaryPool )
        self.secondaryPool.setTooltip( "The secondary pool lets you specify a Pool to use if the primary Pool does not have any available Slaves." )
        self.secondaryPool.setValue( " " )
        
        # Group
        self.group = nuke.Enumeration_Knob( "Deadline_Group", "Group", groups )
        self.addKnob( self.group )
        self.group.setTooltip( "The group that your job will be submitted to." )
        self.group.setValue( "none" )
        
        # Priority
        self.priority = nuke.Int_Knob( "Deadline_Priority", "Priority" )
        self.addKnob( self.priority )
        self.priority.setTooltip( "A job can have a numeric priority ranging from 0 to " + str(maximumPriority) + ", where 0 is the lowest priority." )
        self.priority.setValue( 50 )
        
        # Task Timeout
        self.taskTimeout = nuke.Int_Knob( "Deadline_TaskTimeout", "Task Timeout" )
        self.addKnob( self.taskTimeout )
        self.taskTimeout.setTooltip( "The number of minutes a slave has to render a task for this job before it requeues it. Specify 0 for no limit." )
        self.taskTimeout.setValue( 0 )
        
        # Auto Task Timeout
        self.autoTaskTimeout = nuke.Boolean_Knob( "Deadline_AutoTaskTimeout", "Enable Auto Task Timeout" )
        self.addKnob( self.autoTaskTimeout )
        self.autoTaskTimeout.setTooltip( "If the Auto Task Timeout is properly configured in the Repository Options, then enabling this will allow a task timeout to be automatically calculated based on the render times of previous frames for the job." )
        self.autoTaskTimeout.setValue( False )
        
        # Concurrent Tasks
        self.concurrentTasks = nuke.Int_Knob( "Deadline_ConcurrentTasks", "Concurrent Tasks" )
        self.addKnob( self.concurrentTasks )
        self.concurrentTasks.setTooltip( "The number of tasks that can render concurrently on a single slave. This is useful if the rendering application only uses one thread to render and your slaves have multiple CPUs." )
        self.concurrentTasks.setValue( 1 )
        
        # Limit Concurrent Tasks
        self.limitConcurrentTasks = nuke.Boolean_Knob( "Deadline_LimitConcurrentTasks", "Limit Tasks To Slave's Task Limit" )
        self.addKnob( self.limitConcurrentTasks )
        self.limitConcurrentTasks.setTooltip( "If you limit the tasks to a slave's task limit, then by default, the slave won't dequeue more tasks then it has CPUs. This task limit can be overridden for individual slaves by an administrator." )
        self.limitConcurrentTasks.setValue( False )
        
        # Machine Limit
        self.machineLimit = nuke.Int_Knob( "Deadline_MachineLimit", "Machine Limit" )
        self.addKnob( self.machineLimit )
        self.machineLimit.setTooltip( "Use the Machine Limit to specify the maximum number of machines that can render your job at one time. Specify 0 for no limit." )
        self.machineLimit.setValue( 0 )
        
        # Machine List Is Blacklist
        self.isBlacklist = nuke.Boolean_Knob( "Deadline_IsBlacklist", "Machine List Is A Blacklist" )
        self.addKnob( self.isBlacklist )
        self.isBlacklist.setTooltip( "You can force the job to render on specific machines by using a whitelist, or you can avoid specific machines by using a blacklist." )
        self.isBlacklist.setValue( False )
        
        # Machine List
        self.machineList = nuke.String_Knob( "Deadline_MachineList", "Machine List" )
        self.addKnob( self.machineList )
        self.machineList.setTooltip( "The whitelisted or blacklisted list of machines." )
        self.machineList.setValue( "" )
        
        self.machineListButton = nuke.PyScript_Knob( "Deadline_MachineListButton", "Browse" )
        self.addKnob( self.machineListButton )
        
        # Limit Groups
        self.limitGroups = nuke.String_Knob( "Deadline_LimitGroups", "Limits" )
        self.addKnob( self.limitGroups )
        self.limitGroups.setTooltip( "The Limits that your job requires." )
        self.limitGroups.setValue( "" )
        
        self.limitGroupsButton = nuke.PyScript_Knob( "Deadline_LimitGroupsButton", "Browse" )
        self.addKnob( self.limitGroupsButton )
        
        # Dependencies
        self.dependencies = nuke.String_Knob( "Deadline_Dependencies", "Dependencies" )
        self.addKnob( self.dependencies )
        self.dependencies.setTooltip( "Specify existing jobs that this job will be dependent on. This job will not start until the specified dependencies finish rendering." )
        self.dependencies.setValue( "" )
        
        self.dependenciesButton = nuke.PyScript_Knob( "Deadline_DependenciesButton", "Browse" )
        self.addKnob( self.dependenciesButton )
        
        # On Complete
        self.onComplete = nuke.Enumeration_Knob( "Deadline_OnComplete", "On Job Complete", ("Nothing", "Archive", "Delete") )
        self.addKnob( self.onComplete )
        self.onComplete.setTooltip( "If desired, you can automatically archive or delete the job when it completes." )
        self.onComplete.setValue( "Nothing" )
        
        # Submit Suspended
        self.submitSuspended = nuke.Boolean_Knob( "Deadline_SubmitSuspended", "Submit Job As Suspended" )
        self.addKnob( self.submitSuspended )
        self.submitSuspended.setTooltip( "If enabled, the job will submit in the suspended state. This is useful if you don't want the job to start rendering right away. Just resume it from the Monitor when you want it to render." )
        self.submitSuspended.setValue( False )
        
        # Separator
        self.separator1 = nuke.Text_Knob( "Deadline_Separator2", "" )
        self.addKnob( self.separator1 )
        
        ##########################################################################################
        ## Nuke Options
        ##########################################################################################
        
        # Frame List
        self.frameListMode = nuke.Enumeration_Knob( "Deadline_FrameListMode", "Frame List", ("Global", "Input", "Custom") )
        self.addKnob( self.frameListMode )
        self.frameListMode.setTooltip( "Select the Global, Input, or Custom frame list mode." )
        self.frameListMode.setValue( "Global" )
        
        self.frameList = nuke.String_Knob( "Deadline_FrameList", "" )
        self.frameList.clearFlag(nuke.STARTLINE)
        self.addKnob( self.frameList )
        self.frameList.setTooltip( "If Custom frame list mode is selected, this is the list of frames to render." )
        self.frameList.setValue( "" )
        
        # Chunk Size
        self.chunkSize = nuke.Int_Knob( "Deadline_ChunkSize", "Frames Per Task" )
        self.addKnob( self.chunkSize )
        self.chunkSize.setTooltip( "This is the number of frames that will be rendered at a time for each job task." )
        self.chunkSize.setValue( 10 )
        
        # NukeX
        self.useNukeX = nuke.Boolean_Knob( "Deadline_UseNukeX", "Render With NukeX" )
        self.addKnob( self.useNukeX )
        self.useNukeX.setTooltip( "If checked, NukeX will be used instead of just Nuke." )
        self.useNukeX.setValue( False )
        
        # Batch Mode
        self.batchMode = nuke.Boolean_Knob( "Deadline_BatchMode", "Use Batch Mode" )
        self.addKnob( self.batchMode )
        self.batchMode.setTooltip( "This uses the Nuke plugin's Batch Mode. It keeps the Nuke script loaded in memory between frames, which reduces the overhead of rendering the job." )
        self.batchMode.setValue( False )
        
        # Threads
        self.threads = nuke.Int_Knob( "Deadline_Threads", "Render Threads" )
        self.addKnob( self.threads )
        self.threads.setTooltip( "The number of threads to use for rendering. Set to 0 to have Nuke automatically determine the optimal thread count." )
        self.threads.setValue( 0 )
        
        # Use GPU
        self.useGpu = nuke.Boolean_Knob( "Deadline_UseGpu", "Use The GPU For Rendering" )
        if int(nuke.env[ 'NukeVersionMajor' ]) >= 7:
            self.addKnob( self.useGpu )
        self.useGpu.setTooltip( "If Nuke should also use the GPU for rendering." )
        self.useGpu.setValue( False )

        # Proxy Mode
        self.proxyMode = nuke.Boolean_Knob( "Deadline_ProxyMode", "Render in Proxy Mode" )
        self.addKnob( self.proxyMode )
        self.proxyMode.setTooltip( "If this option is enabled, Nuke will render using the proxy file paths." )
        self.proxyMode.setValue( False )
        
        # Memory Usage
        self.memoryUsage = nuke.Int_Knob( "Deadline_MemoryUsage", "Maximum RAM Usage" )
        self.memoryUsage.setFlag(nuke.STARTLINE)
        self.addKnob( self.memoryUsage )
        self.memoryUsage.setTooltip( "The maximum RAM usage (in MB) to be used for rendering. Set to 0 to not enformace a maximum amount of RAM." )
        self.memoryUsage.setValue( 0 )
        
        # Enforce Write Node Render Order
        self.enforceRenderOrder = nuke.Boolean_Knob( "Deadline_EnforceRenderOrder", "Enforce Write Node Render Order" )
        self.addKnob( self.enforceRenderOrder )
        self.enforceRenderOrder.setTooltip( "Forces Nuke to obey the render order of Write nodes." )
        self.enforceRenderOrder.setValue( False )
        
        # Stack Size
        self.stackSize = nuke.Int_Knob( "Deadline_StackSize", "Minimum Stack Size" )
        self.addKnob( self.stackSize )
        self.stackSize.setTooltip( "The minimum stack size (in MB) to be used for rendering. Set to 0 to not enformace a minimum stack size." )
        self.stackSize.setValue( 0 )
        
        # Continue On Error
        self.continueOnError = nuke.Boolean_Knob( "Deadline_ContinueOnError", "Continue On Error" )
        self.addKnob( self.continueOnError )
        self.continueOnError.setTooltip( "Enable to allow Nuke to continue rendering if it encounters an error." )
        self.continueOnError.setValue( False )

        # Submit Scene
        self.submitScene = nuke.Boolean_Knob( "Deadline_SubmitScene", "Submit Nuke Script File With Job" )
        self.addKnob( self.submitScene )
        self.submitScene.setTooltip( "If this option is enabled, the Nuke script file will be submitted with the job, and then copied locally to the slave machine during rendering." )
        self.submitScene.setValue( False )

        # Performance Profiler
        self.performanceProfiler = nuke.Boolean_Knob( "Deadline_PerformanceProfiler", "Use Performance Profiler" )
        self.performanceProfiler.setFlag(nuke.STARTLINE)
        if int(nuke.env[ 'NukeVersionMajor' ]) >= 9:
            self.addKnob( self.performanceProfiler )
        self.performanceProfiler.setTooltip( "If checked, Nuke will profile the performance of the Nuke script whilst rendering and create a *.xml file per task for later analysis." )
        self.performanceProfiler.setValue( False )

        # Performance Profiler Path
        self.performanceProfilerPath = nuke.File_Knob( "Deadline_PerformanceProfilerDir", "XML Directory" )
        if int(nuke.env[ 'NukeVersionMajor' ]) >= 9:
            self.addKnob( self.performanceProfilerPath )
        self.performanceProfilerPath.setTooltip( "The directory on the network where the performance profile *.xml files will be saved." )
        self.performanceProfilerPath.setValue( "" )
        self.performanceProfilerPath.setEnabled(False)

        # Views
        self.chooseViewsToRender = nuke.Boolean_Knob( "Deadline_ChooseViewsToRender", "Choose Views To Render" )
        self.chooseViewsToRender.setFlag(nuke.STARTLINE)
        self.addKnob( self.chooseViewsToRender)
        self.chooseViewsToRender.setTooltip( "Choose the view(s) you wish to render. This is optional." )

        currentViews = nuke.views()
        self.viewToRenderKnobs = []
        for x, v in enumerate(currentViews):
            currKnob = nuke.Boolean_Knob(('Deadline_ViewToRender_%d' % x), v)
            currKnob.setFlag(0x1000)
            self.viewToRenderKnobs.append((currKnob, v))
            self.addKnob(currKnob)
            currKnob.setValue(True)
            currKnob.setVisible(False) # Hide for now until the checkbox above is enabled.

        # Separator
        self.separator1 = nuke.Text_Knob( "Deadline_Separator3", "" )
        self.addKnob( self.separator1 )
        
        # Separate Jobs
        self.separateJobs = nuke.Boolean_Knob( "Deadline_SeparateJobs", "Submit Write Nodes As Separate Jobs" )
        self.addKnob( self.separateJobs )
        self.separateJobs.setTooltip( "Enable to submit each write node to Deadline as a separate job." )
        self.separateJobs.setValue( False )
        
        # Use Node's Frame List
        self.useNodeRange = nuke.Boolean_Knob( "Deadline_UseNodeRange", "Use Node's Frame List" )
        self.addKnob( self.useNodeRange )
        self.useNodeRange.setTooltip( "If submitting each write node as a separate job, enable this to pull the frame range from the write node, instead of using the global frame range." )
        self.useNodeRange.setValue( True )
        
        #Separate Job Dependencies
        self.separateJobDependencies = nuke.Boolean_Knob( "Deadline_SeparateJobDependencies", "Set Dependencies Based on Write Node Render Order" )
        self.separateJobDependencies.setFlag(nuke.STARTLINE)
        self.addKnob( self.separateJobDependencies )
        self.separateJobDependencies.setTooltip( "Enable each separate job to be dependent on the previous job." )
        self.separateJobDependencies.setValue( False )
        
        # Separate Tasks
        self.separateTasks = nuke.Boolean_Knob( "Deadline_SeparateTasks", "Submit Write Nodes As Separate Tasks For The Same Job" )
        self.separateTasks.setFlag(nuke.STARTLINE)
        self.addKnob( self.separateTasks )
        self.separateTasks.setTooltip( "Enable to submit a job to Deadline where each task for the job represents a different write node, and all frames for that write node are rendered by its corresponding task." )
        self.separateTasks.setValue( False )
        
        # Only Submit Selected Nodes
        self.selectedOnly = nuke.Boolean_Knob( "Deadline_SelectedOnly", "Selected Nodes Only" )
        self.selectedOnly.setFlag(nuke.STARTLINE)
        self.addKnob( self.selectedOnly )
        self.selectedOnly.setTooltip( "If enabled, only the selected Write nodes will be rendered." )
        self.selectedOnly.setValue( False )
        
        # Only Submit Read File Nodes
        self.readFileOnly = nuke.Boolean_Knob( "Deadline_ReadFileOnly", "Nodes With 'Read File' Enabled Only" )
        self.addKnob( self.readFileOnly )
        self.readFileOnly.setTooltip( "If enabled, only the Write nodes that have the 'Read File' option enabled will be rendered." )
        self.readFileOnly.setValue( False )
        
        ##########################################################################################
        ## Project Management Options (aka Shotgun/FTrack)
        ##########################################################################################

        self.integrationTab = nuke.Tab_Knob( "Deadline_IntegrationTab", "Integration" )
        self.addKnob( self.integrationTab )

        self.projectManagementCombo = nuke.Enumeration_Knob( "Deadline_PMIntegration", "Project Management", ["Shotgun", "FTrack"] )
        self.addKnob( self.projectManagementCombo )
        self.projectManagementCombo.setTooltip( "Select which project management integration to use." )

        self.connectButton = nuke.PyScript_Knob( "Deadline_ConnectButton", "Connect..." )
        self.addKnob( self.connectButton )
        self.connectButton.setTooltip( "Opens the connection window." )
        
        self.createNewVersion = nuke.Boolean_Knob( "Deadline_CreateNewVersion", "Create New Version" )
        self.addKnob( self.createNewVersion )
        self.createNewVersion.setEnabled( False )
        self.createNewVersion.setTooltip( "If enabled, Deadline will connect to a new Version for this job." )
        self.createNewVersion.setValue( False )
        
        self.projMgmtVersion = nuke.String_Knob( "Deadline_ProjMgmtVersion", "Version Name" )
        self.addKnob( self.projMgmtVersion )
        self.projMgmtVersion.setEnabled( False )
        self.projMgmtVersion.setTooltip( "The name of the new Version that will be created." )
        self.projMgmtVersion.setValue( "" )
        
        self.projMgmtDescription = nuke.String_Knob( "Deadline_ProjMgmtDescription", "Version Description" )
        self.addKnob( self.projMgmtDescription )
        self.projMgmtDescription.setEnabled( False )
        self.projMgmtDescription.setTooltip( "The description of the new Version that will be created." )
        self.projMgmtDescription.setValue( "" )
        
        self.projMgmtInfo = nuke.Multiline_Eval_String_Knob( "Deadline_ProjMgmtInfo", "Selected Entity" )
        self.addKnob( self.projMgmtInfo )
        self.projMgmtInfo.setEnabled( False )
        self.projMgmtInfo.setTooltip( "Miscellaneous information associated with the Version to be created." )
        self.projMgmtDescription.setValue( "" )
        
        self.draftCreateMovie = nuke.Boolean_Knob( "Deadline_DraftCreateMovie", "Create/Upload Movie" )
        self.addKnob( self.draftCreateMovie )
        self.draftCreateMovie.setValue( False )
        self.draftCreateMovie.setFlag(nuke.STARTLINE) 
        self.draftCreateMovie.setEnabled( False )
        
        self.draftCreateFilmStrip = nuke.Boolean_Knob( "Deadline_DraftCreateFilmStrip", "Create/Upload Film Strip" )
        self.addKnob( self.draftCreateFilmStrip )
        self.draftCreateFilmStrip.setValue( False )
        self.draftCreateFilmStrip.setEnabled( False )
        
        ##########################################################################################
        ## Draft Options
        ##########################################################################################
        
        # self.draftTab = nuke.Tab_Knob( "draftTab", "Draft" )
        # self.addKnob( self.draftTab )
        
        self.draftSeparator1 = nuke.Text_Knob( "Deadline_DraftSeparator1", "" )
        self.addKnob( self.draftSeparator1 )
        
        self.submitDraftJob = nuke.Boolean_Knob( "Deadline_SubmitDraftJob", "Submit Dependent Draft Job" )
        self.addKnob( self.submitDraftJob )
        self.submitDraftJob.setValue( False )
        
        self.uploadToShotgun = nuke.Boolean_Knob( "Deadline_UploadToShotgun", "Upload to Shotgun" )
        self.addKnob( self.uploadToShotgun )
        self.uploadToShotgun.setEnabled( False )
        self.uploadToShotgun.setTooltip( "If enabled, the Draft results will be uploaded to Shotgun when it is complete." )
        self.uploadToShotgun.setValue( True )
        
        self.templatePath = nuke.File_Knob( "Deadline_TemplatePath", "Draft Template" )
        self.addKnob( self.templatePath )
        self.templatePath.setEnabled( False )
        self.templatePath.setTooltip( "The Draft template file to use." )
        self.templatePath.setValue( "" )
        
        self.draftUser = nuke.String_Knob( "Deadline_DraftUser", "User" )
        self.addKnob( self.draftUser )
        self.draftUser.setEnabled( False )
        self.draftUser.setTooltip( "The user name used by the Draft template." )
        self.draftUser.setValue( "" )
        
        self.draftEntity = nuke.String_Knob( "Deadline_DraftEntity", "Entity" )
        self.addKnob( self.draftEntity )
        self.draftEntity.setEnabled( False )
        self.draftEntity.setTooltip( "The entity name used by the Draft template." )
        self.draftEntity.setValue( "" )
        
        self.draftVersion = nuke.String_Knob( "Deadline_DraftVersion", "Version" )
        self.addKnob( self.draftVersion )
        self.draftVersion.setEnabled( False )
        self.draftVersion.setTooltip( "The version name used by the Draft template." )
        self.draftVersion.setValue( "" )
        
        self.draftExtraArgs = nuke.String_Knob( "Deadline_DraftExtraArgs", "Additional Args" )
        self.addKnob( self.draftExtraArgs )
        self.draftExtraArgs.setEnabled( False )
        self.draftExtraArgs.setTooltip( "The additional arguments used by the Draft template." )
        self.draftExtraArgs.setValue( "" )
        
        self.useShotgunDataButton = nuke.PyScript_Knob( "Deadline_UseShotgunDataButton", "Use Shotgun Data" )
        self.useShotgunDataButton.setFlag(nuke.STARTLINE)
        self.addKnob( self.useShotgunDataButton )
        self.useShotgunDataButton.setEnabled( False )
        self.useShotgunDataButton.setTooltip( "Pulls the Draft settings directly from the Shotgun data above (if there is any)." )
        
        
    def knobChanged( self, knob ):
        print "------ In knobChanged ------"
        
        if knob == self.machineListButton:
            GetMachineListFromDeadline()
            
        if knob == self.limitGroupsButton:
            GetLimitGroupsFromDeadline()
        
        if knob == self.dependenciesButton:
            GetDependenciesFromDeadline()
        
        if knob == self.frameList:
            self.frameListMode.setValue( "Custom" )
        
        if knob == self.frameListMode:
            # In Custom mode, don't change anything
            if self.frameListMode.value() != "Custom":
                startFrame = nuke.Root().firstFrame()
                endFrame = nuke.Root().lastFrame()
                if self.frameListMode.value() == "Input":
                    try:
                        activeInput = nuke.activeViewer().activeInput()
                        startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                        endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
                    except:
                        pass
                
                if startFrame == endFrame:
                    self.frameList.setValue( str(startFrame) )
                else:
                    self.frameList.setValue( str(startFrame) + "-" + str(endFrame) )
            
        if knob == self.separateJobs or knob == self.separateTasks:
            self.separateJobs.setEnabled( not self.separateTasks.value() )
            self.separateTasks.setEnabled( not self.separateJobs.value() )
            
            self.separateJobDependencies.setEnabled( self.separateJobs.value() )
            if not self.separateJobs.value():
                self.separateJobDependencies.setValue( self.separateJobs.value() )
            
            self.useNodeRange.setEnabled( self.separateJobs.value() or self.separateTasks.value() )
            self.frameList.setEnabled( not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value() )
            self.chunkSize.setEnabled( not self.separateTasks.value() )
        
        if knob == self.useNodeRange:
            self.frameListMode.setEnabled( not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value() )
            self.frameList.setEnabled( not (self.separateJobs.value() and self.useNodeRange.value()) and not self.separateTasks.value() )

        if knob == self.performanceProfiler:
            self.performanceProfilerPath.setEnabled( self.performanceProfiler.value() )

        if knob == self.chooseViewsToRender:
            visible = self.chooseViewsToRender.value()
            for vk in self.viewToRenderKnobs:
                vk[0].setVisible(visible)
        
        if knob == self.projectManagementCombo:
            ChangeProjectManager( knob.value() )

        if knob == self.connectButton:
            if self.projectManagementCombo.value() == "Shotgun":
                GetShotgunInfo()
            elif self.projectManagementCombo.value() == "FTrack":
                GetFTrackInfo()
        
        if knob == self.useShotgunDataButton:
            user = self.shotgunKVPs.get( 'UserName', "" )
            task = self.shotgunKVPs.get( 'TaskName', "" )
            project = self.shotgunKVPs.get( 'ProjectName', "" )
            entity = self.shotgunKVPs.get( 'EntityName', "" )
            version = self.shotgunKVPs.get( 'VersionName', "" )
            draftTemplate = self.shotgunKVPs.get( 'DraftTemplate', "" )
            
            #set any relevant values
            self.draftUser.setValue( user )
            self.draftVersion.setValue( version )
            
            if task.strip() != "":
                self.draftEntity.setValue( "%s" % task )
            elif project.strip() != "" and entity.strip() != "":
                self.draftEntity.setValue( "%s > %s" % (project, entity) )
                
            if draftTemplate.strip() != "" and draftTemplate != "None":
                self.templatePath.setValue( draftTemplate )
        
        if knob == self.projMgmtVersion:
            if self.projectManagementCombo.value() == "Shotgun":
                self.shotgunKVPs['VersionName'] = self.projMgmtVersion.value()
        
        if knob == self.projMgmtDescription:
            if self.projectManagementCombo.value() == "Shotgun":
                self.shotgunKVPs['Description'] = self.projMgmtDescription.value()
            elif self.projectManagementCombo.value() == "FTrack":
                self.ftrackKVPs['FT_Description'] = self.projMgmtDescription.value()
        
        if knob == self.createNewVersion:
            shotgunSelected = (self.projectManagementCombo.value() == "Shotgun")

            if shotgunSelected:
                self.projMgmtVersion.setEnabled( self.createNewVersion.value() )

            self.projMgmtDescription.setEnabled( self.createNewVersion.value() )
            
            #draft controls that require shotgun to be used
            self.uploadToShotgun.setEnabled( self.createNewVersion.value() and self.submitDraftJob.value() and shotgunSelected )
            self.useShotgunDataButton.setEnabled( self.createNewVersion.value() and self.submitDraftJob.value() and shotgunSelected )
            
            dialog.draftCreateMovie.setEnabled(self.createNewVersion.value() and shotgunSelected )
            dialog.draftCreateFilmStrip.setEnabled(self.createNewVersion.value() and shotgunSelected )
        
        
        if knob == self.submitDraftJob:
            self.templatePath.setEnabled( self.submitDraftJob.value() )
            self.draftUser.setEnabled( self.submitDraftJob.value() )
            self.draftEntity.setEnabled( self.submitDraftJob.value() )
            self.draftVersion.setEnabled( self.submitDraftJob.value() )
            self.draftExtraArgs.setEnabled( self.submitDraftJob.value() )
            
            #these two settings also depend on shotgun being enabled
            shotgunSelected = (self.projectManagementCombo.value() == "Shotgun")
            self.useShotgunDataButton.setEnabled( self.createNewVersion.value() and self.submitDraftJob.value() and shotgunSelected )
            self.uploadToShotgun.setEnabled( self.createNewVersion.value() and self.submitDraftJob.value() and shotgunSelected )
            
        print "------ Out knobChanged ------\n"
            
    def ShowDialog( self ):
        print "------ In ShowDialog ------\n"
        print "------ Out ShowDialog ------\n"
        return nukescripts.PythonPanel.showModalDialog( self )

def CallDeadlineCommand( arguments, hideWindow=True ):
    print "------ In CallDeadlineCommand ------"
    # On OSX, we look for the DEADLINE_PATH file. On other platforms, we use the environment variable.
    if os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f: deadlineBin = f.read().strip()
        deadlineCommand = deadlineBin + "/deadlinecommand"
    else:
        deadlineBin = os.environ['DEADLINE_PATH']
        if os.name == 'nt':
            deadlineCommand = deadlineBin + "\\deadlinecommand.exe"
        else:
            deadlineCommand = deadlineBin + "/deadlinecommand"
    
    startupinfo = None
    if hideWindow and os.name == 'nt' and hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    environment = {}
    for key in os.environ.keys():
        environment[key] = str(os.environ[key])
        
    # Need to set the PATH, cuz windows seems to load DLLs from the PATH earlier that cwd....
    if os.name == 'nt':
        environment['PATH'] = str(deadlineBin + os.pathsep + os.environ['PATH'])
    
    arguments.insert( 0, deadlineCommand)
    
    # Specifying PIPE for all handles to workaround a Python bug on Windows. The unused handles are then closed immediatley afterwards.
    proc = subprocess.Popen(arguments, cwd=deadlineBin, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, env=environment)
    proc.stdin.close()
    proc.stderr.close()
    
    output = proc.stdout.read()
    
    print "------ Out CallDeadlineCommand ------\n"
    return output

def GetProjMgmtInfo( scriptPath ):
    print "------ In GetProjMgmtInfo ------"
    output = CallDeadlineCommand( ["ExecuteScript", scriptPath, "Nuke"], False )
    outputLines = output.splitlines()

    keyValuePairs = {}

    for line in outputLines:
        line = line.strip()
        tokens = line.split( '=', 1 )
        
        if len( tokens ) > 1:
            key = tokens[0]
            value = tokens[1]
            
            keyValuePairs[key] = value
            
    print "------ Out GetProjMgmtInfo ------\n" 

    return keyValuePairs

def GetFTrackInfo():
    print "------ In GetFTrackInfo ------"
    global dialog
    global nukeScriptPath

    ftrackPath = nukeScriptPath.replace( "/submission/Nuke/Main", "" ) + "/submission/FTrack/Main"
    ftrackScript = ftrackPath + "/FTrackUI.py"

    tempKVPs = GetProjMgmtInfo( ftrackScript )

    if len( tempKVPs ) > 0:
        dialog.ftrackKVPs = tempKVPs
        UpdateProjectManagementUI( True )
        
    print "------ Out GetFTrackInfo ------\n" 

def GetShotgunInfo():
    print "------ In GetShotgunInfo ------"
    global dialog
    global nukeScriptPath
    
    shotgunPath = nukeScriptPath.replace( "/submission/Nuke/Main", "" ) + "/events/Shotgun"
    shotgunScript = shotgunPath + "/ShotgunUI.py"
    
    tempKVPs = GetProjMgmtInfo( shotgunScript )
    
    if len( tempKVPs ) > 0:
        dialog.shotgunKVPs = tempKVPs
        UpdateProjectManagementUI( True )
        
    print "------ Out GetShotgunInfo ------\n" 


def ChangeProjectManager( switchTo ):
    print "------ In ChangeProjectManager ------"
    global dialog

    #defaults
    versionLabel = "Version Name"
    descLabel = "Version Description"
    miscLabel = "Selected Entity"

    #integartion-specific overrides
    if switchTo == "FTrack":
        versionLabel = "Selected Asset"
        miscLabel = "Miscellaneous Info"
    elif switchTo == "Shotgun":
        pass
    else:
        #invalid 
        return

    dialog.projMgmtVersion.setLabel( versionLabel )

    dialog.projMgmtDescription.setLabel( descLabel )

    dialog.projMgmtInfo.setLabel( miscLabel )

    UpdateProjectManagementUI( dialog.createNewVersion.value() )
    
    print "------ Out ChangeProjectManager ------\n" 


#Updates the Project Management UI to reflect the contents of the Shotgun/FTrack KVPs
def UpdateProjectManagementUI( forceOn=False ):
    print "------ In UpdateProjectManagementUI ------"
    global dialog

    projectManager = dialog.projectManagementCombo.value()

    createValue = False
    createEnabled = False

    versionValue = ""
    versionEnabled = False

    descValue = ""
    descEnabled = False

    infoValue = ""
    infoEnabled = False

    draftIntegrationEnabled = False

    if projectManager == "Shotgun":
        if dialog.shotgunKVPs != None:
            createEnabled = len(dialog.shotgunKVPs) > 0
            
            if forceOn and createEnabled:
                createValue = True
            
            versionValue = dialog.shotgunKVPs.get( 'VersionName', "" )
            versionEnabled = createValue
            descValue = dialog.shotgunKVPs.get( 'Description', "" )
            descEnabled = createValue
            
            if 'UserName' in dialog.shotgunKVPs:
                infoValue += "User Name: %s\n" % dialog.shotgunKVPs[ 'UserName' ]
            if 'TaskName' in dialog.shotgunKVPs:
                infoValue += "Task Name: %s\n" % dialog.shotgunKVPs[ 'TaskName' ]
            if 'ProjectName' in dialog.shotgunKVPs:
                infoValue += "Project Name: %s\n" % dialog.shotgunKVPs[ 'ProjectName' ]
            if 'EntityName' in dialog.shotgunKVPs:
                infoValue += "Entity Name: %s\n" % dialog.shotgunKVPs[ 'EntityName' ]
            if 'EntityType' in dialog.shotgunKVPs:
                infoValue += "Entity Type: %s\n" % dialog.shotgunKVPs[ 'EntityType' ]
            if 'DraftTemplate' in dialog.shotgunKVPs:
                infoValue += "Draft Template: %s\n" % dialog.shotgunKVPs[ 'DraftTemplate' ]

            #update the draft stuff that relies on shotgun
            draftIntegrationEnabled = dialog.submitDraftJob.value() and createValue
            
    elif projectManager == "FTrack":
        if dialog.ftrackKVPs:
            createEnabled = True
            createValue = forceOn

            versionValue = dialog.ftrackKVPs.get( 'FT_AssetName', "" )
            descValue = dialog.ftrackKVPs.get( 'FT_Description', "" )
            descEnabled = createValue

            for key in dialog.ftrackKVPs:
                infoValue += "{0}: {1}\n".format( key, dialog.ftrackKVPs[key] )
    else:
        #Invalid...
        pass

    dialog.createNewVersion.setValue( createValue )
    dialog.createNewVersion.setEnabled( createEnabled )

    dialog.projMgmtVersion.setValue( versionValue )
    dialog.projMgmtVersion.setEnabled( versionEnabled )

    dialog.projMgmtDescription.setValue( descValue )
    dialog.projMgmtDescription.setEnabled( descEnabled )

    dialog.projMgmtInfo.setValue( infoValue )
    dialog.projMgmtInfo.setEnabled( infoEnabled )
    
    dialog.draftCreateMovie.setEnabled(versionEnabled and projectManager == "Shotgun")
    dialog.draftCreateFilmStrip.setEnabled(versionEnabled and projectManager == "Shotgun")
    
    dialog.uploadToShotgun.setEnabled( draftIntegrationEnabled )
    dialog.useShotgunDataButton.setEnabled( draftIntegrationEnabled )
    
    print "------ Out UpdateProjectManagementUI ------\n" 
    
def GetMachineListFromDeadline():
    print "------ In GetMachineListFromDeadline ------"
    global dialog
    output = CallDeadlineCommand( ["-selectmachinelist", dialog.machineList.value()] )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.machineList.setValue( output )
        
    print "------ Out GetMachineListFromDeadline ------\n"
    

def GetLimitGroupsFromDeadline():
    print "------ In GetLimitGroupsFromDeadline ------"
    global dialog
    output = CallDeadlineCommand( ["-selectlimitgroups", dialog.limitGroups.value()] )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.limitGroups.setValue( output )
        
    print "------ Out GetLimitGroupsFromDeadline ------\n"

def GetDependenciesFromDeadline():
    print "------ In GetDependenciesFromDeadline ------"
    global dialog
    output = CallDeadlineCommand( ["-selectdependencies", dialog.dependencies.value()] )
    output = output.replace( "\r", "" ).replace( "\n", "" )
    if output != "Action was cancelled by user":
        dialog.dependencies.setValue( output )
    
    print "------ Out GetDependenciesFromDeadline ------\n"

# Checks a path to make sure it has an extension
def HasExtension( path ):
    print "------ In HasExtension ------\n"
    filename = os.path.basename( path )
    
    print "------ Out HasExtension ------\n"
    
    return filename.rfind( "." ) > -1


# Checks if path is local (c, d, or e drive).
def IsPathLocal( path ):
    print "------ In IsPathLocal ------\n"
    lowerPath = path.lower()
    if lowerPath.startswith( "c:" ) or lowerPath.startswith( "d:" ) or lowerPath.startswith( "e:" ):
        return True
    print "------ Out IsPathLocal ------\n"
    return False

# Checks if the given filename ends with a movie extension
def IsMovie( path ):
    print "------ In IsMovie ------\n"
    lowerPath = path.lower()
    if lowerPath.endswith( ".mov" ):
        return True
    print "------ Out IsMovie ------\n"
    return False

# Checks if the filename is padded (ie: \\output\path\filename_%04.tga).
def IsPadded( path ):
    print "------ In IsPadded ------\n"
    # Need to look for any embedded TCL in the path in case it's being used to build up the padding.
    tclStart = path.find('[')
    while tclStart != -1:
        tclEnd = path.find(']', tclStart)
        if tclEnd != -1:
            pathPrefix = path[:tclStart]
            pathTcl = path[tclStart:tclEnd+1]
            pathPostFix = path[tclEnd+1:]
            path = pathPrefix + nuke.tcl("expr", pathTcl) + pathPostFix
        else:
            break
        tclStart = path.find('[')
    
    paddingRe = re.compile( "%([0-9]+)d", re.IGNORECASE )
    if paddingRe.search( path ) != None:
        return True
    elif path.find( "#" ) > -1:
        return True
    print "------ Out IsPadded ------\n"
    return False

def RightReplace(s, old, new, occurrence):
    print "------ In RightReplace ------"
    li = s.rsplit(old, occurrence)
    print "------ Out RightReplace ------"
    return new.join(li)

def StrToBool(str):
    print "------ In StrToBool ------"
    print "------ Out StrToBool ------\n"
    return str.lower() in ("yes", "true", "t", "1", "on")

# Parses through the filename looking for the last padded pattern, replaces
# it with the correct number of #'s, and returns the new padded filename.
def GetPaddedPath( path ):
    print "------ In GetPaddedPath ------"
    # paddingRe = re.compile( "%([0-9]+)d", re.IGNORECASE )
    
    # paddingMatch = paddingRe.search( path )
    # if paddingMatch != None:
        # paddingSize = int(paddingMatch.lastgroup)
        
        # padding = ""
        # while len(padding) < paddingSize:
            # padding = padding + "#"
        
        # path = paddingRe.sub( padding, path, 1 )
    
    paddingRe = re.compile( "([0-9]+)", re.IGNORECASE )
    
    paddingMatches = paddingRe.findall( path )
    if paddingMatches != None and len( paddingMatches ) > 0:
        paddingString = paddingMatches[ len( paddingMatches ) - 1 ]
        paddingSize = len(paddingString)
        
        padding = ""
        while len(padding) < paddingSize:
            padding = padding + "#"
        
        path = RightReplace( path, paddingString, padding, 1 )
    print "------ Out GetPaddedPath ------"
    return path
    
def buildKnob(name, abr):
    print "------ In buildKnob ------"
    try:
        root = nuke.Root()
        if "Deadline" not in root.knobs():
            tabKnob = nuke.Tab_Knob("Deadline")
            root.addKnob(tabKnob)
        
        if name in root.knobs():
            return root.knob( name )
        else:
            tKnob = nuke.String_Knob( name, abr )
            root.addKnob ( tKnob )
            return  tKnob
    except:
        print "Error in knob creation. "+ name + " " + abr
        
    print "------ Out buildKnob ------"
        
def WriteStickySettings( dialog, configFile ):
    print "------ In WriteStickySettings ------"
    
    try:
        print "Writing sticky settings..."
        config = ConfigParser.ConfigParser()
        config.add_section( "Sticky" )
        
        config.set( "Sticky", "FrameListMode", dialog.frameListMode.value() )
        config.set( "Sticky", "CustomFrameList", dialog.frameList.value().strip() )
        
        config.set( "Sticky", "Department", dialog.department.value() )
        config.set( "Sticky", "Pool", dialog.pool.value() )
        config.set( "Sticky", "SecondaryPool", dialog.secondaryPool.value() )
        config.set( "Sticky", "Group", dialog.group.value() )
        config.set( "Sticky", "Priority", str( dialog.priority.value() ) )
        config.set( "Sticky", "MachineLimit", str( dialog.machineLimit.value() ) )
        config.set( "Sticky", "IsBlacklist", str( dialog.isBlacklist.value() ) )
        config.set( "Sticky", "MachineList", dialog.machineList.value() )
        config.set( "Sticky", "LimitGroups", dialog.limitGroups.value() )
        config.set( "Sticky", "SubmitSuspended", str( dialog.submitSuspended.value() ) )
        config.set( "Sticky", "ChunkSize", str( dialog.chunkSize.value() ) )
        config.set( "Sticky", "ConcurrentTasks", str( dialog.concurrentTasks.value() ) )
        config.set( "Sticky", "LimitConcurrentTasks", str( dialog.limitConcurrentTasks.value() ) )
        config.set( "Sticky", "Threads", str( dialog.threads.value() ) )
        config.set( "Sticky", "SubmitScene", str( dialog.submitScene.value() ) )
        config.set( "Sticky", "BatchMode", str( dialog.batchMode.value() ) )
        config.set( "Sticky", "ContinueOnError", str( dialog.continueOnError.value() ) )
        config.set( "Sticky", "UseNodeRange", str( dialog.useNodeRange.value() ) )
        config.set( "Sticky", "UseGpu", str( dialog.useGpu.value() ) )
        config.set( "Sticky", "EnforceRenderOrder", str( dialog.enforceRenderOrder.value() ) )
        config.set( "Sticky", "ProxyMode", str(dialog.proxyMode.value() ) )
        config.set( "Sticky", "PerformanceProfiler", str(dialog.performanceProfiler.value() ) )
        config.set( "Sticky", "PerformanceProfilerPath", dialog.performanceProfilerPath.value() )
        config.set( "Sticky", "CreateUploadMovie", str(dialog.draftCreateMovie.value() ) )
        config.set( "Sticky", "CreateUploadFilmStrip", str(dialog.draftCreateFilmStrip.value() ) )
        
        config.set( "Sticky", "UseDraft", str( dialog.submitDraftJob.value() ) )
        config.set( "Sticky", "DraftTemplate", dialog.templatePath.value() )
        config.set( "Sticky", "DraftUser", dialog.draftUser.value() )
        config.set( "Sticky", "DraftEntity", dialog.draftEntity.value() )
        config.set( "Sticky", "DraftVersion", dialog.draftVersion.value() )
        config.set( "Sticky", "DraftExtraArgs", dialog.draftExtraArgs.value() )

        config.set( "Sticky", "ProjectManagement", dialog.projectManagementCombo.value() )
        
        fileHandle = open( configFile, "w" )
        config.write( fileHandle )
        fileHandle.close()
    except:
        print( "Could not write sticky settings" )
        print traceback.format_exc()
    
    try:
        #Saves all the sticky setting to the root
        tKnob = buildKnob( "FrameListMode" , "frameListMode")
        tKnob.setValue( dialog.frameListMode.value() )
        
        tKnob = buildKnob( "CustomFrameList", "customFrameList" )
        tKnob.setValue( dialog.frameList.value().strip() )
        
        tKnob = buildKnob( "Department", "department" )
        tKnob.setValue( dialog.department.value() )
        
        tKnob = buildKnob( "Pool", "pool" )
        tKnob.setValue( dialog.pool.value() )
        
        tKnob = buildKnob( "SecondaryPool", "secondaryPool" )
        tKnob.setValue( dialog.secondaryPool.value() )
        
        tKnob = buildKnob( "Group", "group" )
        tKnob.setValue( dialog.group.value() )
        
        tKnob = buildKnob( "Priority", "priority" )
        tKnob.setValue( str( dialog.priority.value() ) )
        
        tKnob = buildKnob( "MachineLimit", "machineLimit" )
        tKnob.setValue( str( dialog.machineLimit.value() ) )
        
        tKnob = buildKnob( "IsBlacklist", "isBlacklist" )
        tKnob.setValue( str( dialog.isBlacklist.value() ) )
        
        tKnob = buildKnob( "MachineList", "machineList" )
        tKnob.setValue( dialog.machineList.value() )
        
        tKnob = buildKnob( "LimitGroups", "limitGroups" )
        tKnob.setValue( dialog.limitGroups.value() )
        
        tKnob = buildKnob( "SubmitSuspended", "submitSuspended" )
        tKnob.setValue( str( dialog.submitSuspended.value() ) )
        
        tKnob = buildKnob( "ChunkSize", "chunkSize" ) 
        tKnob.setValue( str( dialog.chunkSize.value() ) )
        
        tKnob = buildKnob( "ConcurrentTasks", "concurrentTasks" ) 
        tKnob.setValue( str( dialog.concurrentTasks.value() ) )
        
        tKnob = buildKnob( "LimitConcurrentTasks", "limitConcurrentTasks" )
        tKnob.setValue( str( dialog.limitConcurrentTasks.value() ) )
        
        tKnob = buildKnob( "Threads", "threads" )
        tKnob.setValue( str( dialog.threads.value() ) )
        
        tKnob = buildKnob( "SubmitScene", "submitScene" )
        tKnob.setValue( str( dialog.submitScene.value() ) )
        
        tKnob = buildKnob( "BatchMode", "batchMode" )
        tKnob.setValue( str( dialog.batchMode.value() ) )
        
        tKnob = buildKnob( "ContinueOnError", "continueOnError" )
        tKnob.setValue( str( dialog.continueOnError.value() ) )
        
        tKnob = buildKnob( "UseNodeRange", "useNodeRange" )
        tKnob.setValue( str( dialog.useNodeRange.value() ) )
        
        tKnob = buildKnob( "UseGpu", "useGpu" )
        tKnob.setValue( str( dialog.useGpu.value() ) )
        
        tKnob = buildKnob( "EnforceRenderOrder", "enforceRenderOrder" )
        tKnob.setValue( str( dialog.enforceRenderOrder.value() ) )

        tKnob = buildKnob( "ProxyMode", "proxyMode" )
        tKnob.setValue( str( dialog.proxyMode.value() ) )

        tknob = buildKnob( "PerformanceProfiler", "performanceProfiler" )
        tKnob.setValue( str( dialog.performanceProfiler.value() ) )

        tKnob = buildKnob( "PerformanceProfilerPath", "performanceProfilerPath" )
        tKnob.setValue( dialog.performanceProfilerPath.value() )

        tKnob = buildKnob( "CreateUploadMovie", "createUploadMovie" )
        tKnob.setValue( str( dialog.draftCreateMovie.value() ) )
        
        tKnob = buildKnob( "CreateUploadFilmStrip", "createUploadFilmStrip" )
        tKnob.setValue( str( dialog.draftCreateFilmStrip.value() ) )

        tKnob = buildKnob( "UseDraft", "useDraft" )
        tKnob.setValue( str( dialog.submitDraftJob.value() ) )
        
        tKnob = buildKnob( "DraftTemplate", "draftTemplate" )
        tKnob.setValue( dialog.templatePath.value() )
        
        tKnob = buildKnob( "DraftUser", "draftUser" )
        tKnob.setValue( dialog.draftUser.value() )
        
        tKnob = buildKnob( "DraftEntity", "draftEntity" )
        tKnob.setValue( dialog.draftEntity.value() )
        
        tKnob = buildKnob( "DraftVersion", "draftVersion" )
        tKnob.setValue( dialog.draftVersion.value() )
        
        tKnob = buildKnob( "DraftExtraArgs", "draftExtraArgs" )          
        tKnob.setValue( dialog.draftExtraArgs.value() )

        tKnob = buildKnob( "ProjectManagement", "projectManagement")
        tKnob.setValue( dialog.projectManagementCombo.value() )
        
        tKnob = buildKnob( "DeadlineSGData", "shotgunKVPs" )
        tKnob.setValue( str(dialog.shotgunKVPs) )

        tKnob = buildKnob( "DeadlineFTData", "ftrackKVPs" )
        tKnob.setValue( str(dialog.ftrackKVPs) )

        # If the Nuke script has been modified, then save it to preserve SG settings.
        root = nuke.Root()
        if root.modified():
            nuke.scriptSave( root.name() )
        
    except:
        print( "Could not write knob settings." )
        print traceback.format_exc()
        
    print "------ Out WriteStickySettings ------"

def SubmitJob( dialog, root, node, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, jobCount, semaphore ):
    print "------ In SubmitJob ------"
    print "Preparing job #%d for submission.." % jobCount
    
    # Create a task in Nuke's progress  bar dialog
    #progressTask = nuke.ProgressTask("Submitting %s to Deadline" % tempJobName)
    progressTask = nuke.ProgressTask("Job Submission")
    progressTask.setMessage("Creating Job Info File")
    progressTask.setProgress(0)
    
    # Create the submission info file (append job count since we're submitting multiple jobs at the same time in different threads)
    jobInfoFile = deadlineTemp + ("/nuke_submit_info%d.job" % jobCount)
    fileHandle = open( jobInfoFile, "w" )
    fileHandle.write( "Plugin=Nuke\n" )
    fileHandle.write( "Name=%s\n" % tempJobName )
    fileHandle.write( "Comment=%s\n" % dialog.comment.value() )
    fileHandle.write( "Department=%s\n" % dialog.department.value() )
    
    fileHandle.write( "ExtraInfo7=%s\n" % dialog.projectPhase.value() )
    fileHandle.write( "ExtraInfo8=%s\n" % dialog.frameSize.value() )
    fileHandle.write( "ExtraInfo9=%s\n" % dialog.fileType.value() )
    
    fileHandle.write( "Pool=%s\n" % dialog.pool.value() )
    if dialog.secondaryPool.value() == "":
        fileHandle.write( "SecondaryPool=\n" )
    else:
        fileHandle.write( "SecondaryPool=%s\n" % dialog.secondaryPool.value() )
    fileHandle.write( "Group=%s\n" % dialog.group.value() )
    fileHandle.write( "Priority=%s\n" % dialog.priority.value() )
    fileHandle.write( "MachineLimit=%s\n" % dialog.machineLimit.value() )
    fileHandle.write( "TaskTimeoutMinutes=%s\n" % dialog.taskTimeout.value() )
    fileHandle.write( "EnableAutoTimeout=%s\n" % dialog.autoTaskTimeout.value() )
    fileHandle.write( "ConcurrentTasks=%s\n" % dialog.concurrentTasks.value() )
    fileHandle.write( "LimitConcurrentTasksToNumberOfCpus=%s\n" % dialog.limitConcurrentTasks.value() )
    fileHandle.write( "LimitGroups=%s\n" % dialog.limitGroups.value() )
    fileHandle.write( "JobDependencies=%s\n" %  tempDependencies)
    fileHandle.write( "OnJobComplete=%s\n" % dialog.onComplete.value() )
    
    if dialog.separateTasks.value():
        writeNodeCount = 0
        for tempNode in writeNodes:
            if 'Precomp' not in tempNode.fullName():
                print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                if not tempNode.knob( 'disable' ).value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and tempNode.knob( 'reading' ):
                        enterLoop = enterLoop and tempNode.knob( 'reading' ).value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and tempNode.isSelected()
                    
                    if enterLoop:
                        writeNodeCount += 1
        
        
        fileHandle.write( "Frames=0-%s\n" % (writeNodeCount-1) )
        fileHandle.write( "ChunkSize=1\n" )
    else:
        fileHandle.write( "Frames=%s\n" % tempFrameList )
        fileHandle.write( "ChunkSize=%s\n" % tempChunkSize )
    
    if dialog.submitSuspended.value():
        fileHandle.write( "InitialStatus=Suspended\n" )
    
    if dialog.isBlacklist.value():
        fileHandle.write( "Blacklist=%s\n" % dialog.machineList.value() )
    else:
        fileHandle.write( "Whitelist=%s\n" % dialog.machineList.value() )
    
    extraKVPIndex = 0
    
    index = 0
    for v in nuke.views():
        if dialog.separateJobs.value():
        
            if ( root.proxy() and node.knob( 'proxy' ).value() != "" ):
                fileValue = node.knob( 'proxy' ).value()
                evaluatedValue = node.knob( 'proxy' ).evaluate(view=v)
            else:
                fileValue = node.knob( 'file' ).value()
                evaluatedValue = node.knob( 'file' ).evaluate(view=v)
            
            if fileValue != None and fileValue != "" and evaluatedValue != None and evaluatedValue != "":
                tempPath, tempFilename = os.path.split( evaluatedValue )
                if IsPadded( os.path.basename( fileValue ) ):
                    tempFilename = GetPaddedPath( tempFilename )
                    
                paddedPath = os.path.join( tempPath, tempFilename )
                fileHandle.write( "OutputFilename%i=%s\n" % (index, paddedPath ))
                
                #Check if the Write Node will be modifying the output's Frame numbers
                if node.knob( 'frame_mode' ):
                    if ( node.knob( 'frame_mode' ).value() == "offset" ):
                        fileHandle.write( "ExtraInfoKeyValue%d=OutputFrameOffset%i=%s\n" % (extraKVPIndex,index, str( int(node.knob( 'frame' ).value()) )) )
                        extraKVPIndex += 1
                    elif ( node.knob( 'frame_mode' ).value() == "start at" or node.knob( 'frame_mode' ).value() == "start_at"):
                        franges = nuke.FrameRanges( tempFrameList )
                        fileHandle.write( "ExtraInfoKeyValue%d=OutputFrameOffset%i=%s\n" % (extraKVPIndex,index, str( int(node.knob( 'frame' ).value()) - franges.minFrame() )) )
                        extraKVPIndex += 1
                    else:
                        #TODO: Handle 'expression'? Would be much harder
                        pass
                index+=1
        else:
            for tempNode in writeNodes:
                if 'Precomp' not in tempNode.fullName():
                    print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                    if not tempNode.knob( 'disable' ).value():
                        enterLoop = True
                        if dialog.readFileOnly.value() and tempNode.knob( 'reading' ):
                            enterLoop = enterLoop and tempNode.knob( 'reading' ).value()
                        if dialog.selectedOnly.value():
                            enterLoop = enterLoop and tempNode.isSelected()
                        
                        if enterLoop:
                            if ( root.proxy() and tempNode.knob( 'proxy' ).value() != "" ):
                                fileValue = tempNode.knob( 'proxy' ).value()
                                evaluatedValue = tempNode.knob( 'proxy' ).evaluate(view=v)
                            else:
                                fileValue = tempNode.knob( 'file' ).value()
                                evaluatedValue = tempNode.knob( 'file' ).evaluate(view=v)
                            
                            if fileValue != None and fileValue != "" and evaluatedValue != None and evaluatedValue != "":
                                tempPath, tempFilename = os.path.split( evaluatedValue )
                                
                                if dialog.separateTasks.value():
                                    fileHandle.write( "OutputDirectory%s=%s\n" % (index, tempPath) )
                                else:
                                    if IsPadded( os.path.basename( fileValue ) ):
                                        tempFilename = GetPaddedPath( tempFilename )
                                        
                                    paddedPath = os.path.join( tempPath, tempFilename )
                                    fileHandle.write( "OutputFilename%s=%s\n" % (index, paddedPath ) )
                                    
                                    #Check if the Write Node will be modifying the output's Frame numbers
                                    if tempNode.knob( 'frame_mode' ):
                                        if ( tempNode.knob( 'frame_mode' ).value() == "offset" ):
                                            fileHandle.write( "ExtraInfoKeyValue%d=OutputFrameOffset%s=%s\n" % (extraKVPIndex, index, str( int(tempNode.knob( 'frame' ).value()) )) )
                                            extraKVPIndex += 1
                                        elif ( tempNode.knob( 'frame_mode' ).value() == "start at" or tempNode.knob( 'frame_mode' ).value() == "start_at"):
                                            franges = nuke.FrameRanges( tempFrameList )
                                            fileHandle.write( "ExtraInfoKeyValue%d=OutputFrameOffset%s=%s\n" % (extraKVPIndex, index, str( int(tempNode.knob( 'frame' ).value()) - franges.minFrame() )) )
                                            extraKVPIndex += 1
                                        else:
                                            #TODO: Handle 'expression'? Would be much harder
                                            pass
                                    
                                index = index + 1        
        
    # Write the shotgun data.
    if dialog.createNewVersion.value():
        if dialog.projectManagementCombo.value() == "Shotgun":

            if 'TaskName' in dialog.shotgunKVPs:
                fileHandle.write( "ExtraInfo0=%s\n" % dialog.shotgunKVPs['TaskName'] )
                
            if 'ProjectName' in dialog.shotgunKVPs:
                fileHandle.write( "ExtraInfo1=%s\n" % dialog.shotgunKVPs['ProjectName'] )
                
            if 'EntityName' in dialog.shotgunKVPs:
                fileHandle.write( "ExtraInfo2=%s\n" % dialog.shotgunKVPs['EntityName'] )
                
            if 'VersionName' in dialog.shotgunKVPs:
                fileHandle.write( "ExtraInfo3=%s\n" % dialog.shotgunKVPs['VersionName'] )
                
            if 'Description' in dialog.shotgunKVPs:
                fileHandle.write( "ExtraInfo4=%s\n" % dialog.shotgunKVPs['Description'] )
                
            if 'UserName' in dialog.shotgunKVPs:
                fileHandle.write( "ExtraInfo5=%s\n" % dialog.shotgunKVPs['UserName'] )
            
            #dump the rest in as KVPs
            for key in dialog.shotgunKVPs:
                if key != "DraftTemplate":
                    fileHandle.write( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, dialog.shotgunKVPs[key]) )
                    extraKVPIndex += 1
            
            groupBatch = False
            if dialog.draftCreateMovie.value():
                fileHandle.write( "ExtraInfoKeyValue%s=Draft_CreateSGMovie=True\n" % (extraKVPIndex) )
                extraKVPIndex += 1
                groupBatch = True
                
            if dialog.draftCreateFilmStrip.value():
                fileHandle.write( "ExtraInfoKeyValue%s=Draft_CreateSGFilmstrip=True\n" % (extraKVPIndex) )
                extraKVPIndex += 1
                groupBatch = True
            if groupBatch:
                fileHandle.write( "BatchName=%s\n" % (tempJobName ) ) 
            
        elif dialog.projectManagementCombo.value() == "FTrack":
            
            if 'FT_TaskName' in dialog.ftrackKVPs:
                fileHandle.write( "ExtraInfo0=%s\n" % dialog.ftrackKVPs['FT_TaskName'] )

            if 'FT_ProjectName' in dialog.ftrackKVPs:
                fileHandle.write( "ExtraInfo1=%s\n" % dialog.ftrackKVPs['FT_ProjectName'] )

            if 'FT_AssetName' in dialog.ftrackKVPs:
                fileHandle.write( "ExtraInfo2=%s\n" % dialog.ftrackKVPs['FT_AssetName'] )

            #will update Version # in EI3 when it gets created

            if 'FT_Description' in dialog.ftrackKVPs:
                fileHandle.write( "ExtraInfo4=%s\n" % dialog.ftrackKVPs['FT_Description'] )

            if 'FT_Username' in dialog.ftrackKVPs:
                fileHandle.write( "ExtraInfo5=%s\n" % dialog.ftrackKVPs['FT_Username'] )

            for key in dialog.ftrackKVPs:
                fileHandle.write( "ExtraInfoKeyValue%d=%s=%s\n" % (extraKVPIndex, key, dialog.ftrackKVPs[key]) )
                extraKVPIndex += 1
    
    #Draft stuff
    if dialog.submitDraftJob.value():
        draftNode = node
        #TODO: Need to figure out if we want to do something else in this case (all write nodes being submitted in one job)
        if node == None:
            draftNode = writeNodes[0] 
        
        fileHandle.write( "ExtraInfoKeyValue%d=DraftTemplate=%s\n" % (extraKVPIndex, dialog.templatePath.value()) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftUsername=%s\n" % (extraKVPIndex, dialog.draftUser.value()) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftEntity=%s\n" % (extraKVPIndex, dialog.draftEntity.value()) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftVersion=%s\n" % (extraKVPIndex, dialog.draftVersion.value()) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftFrameWidth=%s\n" % (extraKVPIndex, draftNode.width()) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftFrameHeight=%s\n" % (extraKVPIndex, draftNode.height()) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftUploadToShotgun=%s\n" % (extraKVPIndex, str(dialog.uploadToShotgun.enabled() and dialog.uploadToShotgun.value())) )
        extraKVPIndex += 1
        fileHandle.write( "ExtraInfoKeyValue%d=DraftExtraArgs=%s\n" % (extraKVPIndex, dialog.draftExtraArgs.value()) )
        extraKVPIndex += 1
    
    fileHandle.close()
    
    # Update task progress
    progressTask.setMessage("Creating Plugin Info File")
    progressTask.setProgress(10)
    
    # Create the plugin info file
    pluginInfoFile = deadlineTemp + ("/nuke_plugin_info%d.job" % jobCount)
    fileHandle = open( pluginInfoFile, "w" )
    if not dialog.submitScene.value():
        fileHandle.write( "SceneFile=%s\n" % root.name() )
    
    fileHandle.write( "Version=%s.%s\n" % (nuke.env[ 'NukeVersionMajor' ], nuke.env['NukeVersionMinor']) )
    fileHandle.write( "Threads=%s\n" % dialog.threads.value() )
    fileHandle.write( "RamUse=%s\n" % dialog.memoryUsage.value() )
    fileHandle.write( "BatchMode=%s\n" % dialog.batchMode.value())
    fileHandle.write( "BatchModeIsMovie=%s\n" % tempIsMovie )
    
    if dialog.separateJobs.value():
        #we need the fullName of the node here, otherwise write nodes that are embedded in groups won't work
        fileHandle.write( "WriteNode=%s\n" % node.fullName() )
    elif dialog.separateTasks.value():
        fileHandle.write( "WriteNodesAsSeparateJobs=True\n" )
        
        writeNodeIndex = 0
        for tempNode in writeNodes:
            if 'Precomp' not in tempNode.fullName():
                print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                if not tempNode.knob( 'disable' ).value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and tempNode.knob( 'reading' ):
                        enterLoop = enterLoop and tempNode.knob( 'reading' ).value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and tempNode.isSelected()
                    
                    if enterLoop:
                        #we need the fullName of the node here, otherwise write nodes that are embedded in groups won't work
                        fileHandle.write( "WriteNode%s=%s\n" % (writeNodeIndex,tempNode.fullName()) )
                        
                        if dialog.useNodeRange.value() and tempNode.knob( 'use_limit' ).value():
                            startFrame = int(tempNode.knob('first').value())
                            endFrame = int(tempNode.knob('last').value())
                        else:
                            startFrame = nuke.Root().firstFrame()
                            endFrame = nuke.Root().lastFrame()
                            if dialog.frameListMode.value() == "Input":
                                try:
                                    activeInput = nuke.activeViewer().activeInput()
                                    startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                                    endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
                                except:
                                    pass
                        
                        fileHandle.write( "WriteNode%sStartFrame=%s\n" % (writeNodeIndex,startFrame) )
                        fileHandle.write( "WriteNode%sEndFrame=%s\n" % (writeNodeIndex,endFrame) )
                        writeNodeIndex += 1
    else:
        if dialog.readFileOnly.value() or dialog.selectedOnly.value():
            writeNodesStr = ""
            
            for tempNode in writeNodes:
                if 'Precomp' not in tempNode.fullName():
                    print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                    if not tempNode.knob( 'disable' ).value():
                        enterLoop = True
                        if dialog.readFileOnly.value() and tempNode.knob( 'reading' ):
                            enterLoop = enterLoop and tempNode.knob( 'reading' ).value()
                        if dialog.selectedOnly.value():
                            enterLoop = enterLoop and tempNode.isSelected()
                        
                        if enterLoop:
                            #we need the fullName of the node here, otherwise write nodes that are embedded in groups won't work
                            writeNodesStr += ("%s," % tempNode.fullName())
                        
            writeNodesStr = writeNodesStr.strip( "," )
            fileHandle.write( "WriteNode=%s\n" % writeNodesStr )

    fileHandle.write( "NukeX=%s\n" % dialog.useNukeX.value() )

    if int(nuke.env[ 'NukeVersionMajor' ]) >= 7:
        fileHandle.write( "UseGpu=%s\n" % dialog.useGpu.value() )

    fileHandle.write( "ProxyMode=%s\n" % dialog.proxyMode.value() )
    fileHandle.write( "EnforceRenderOrder=%s\n" % dialog.enforceRenderOrder.value() )
    fileHandle.write( "ContinueOnError=%s\n" % dialog.continueOnError.value() )

    if int(nuke.env[ 'NukeVersionMajor' ]) >= 9:
        fileHandle.write( "PerformanceProfiler=%s\n" % dialog.performanceProfiler.value() )
        fileHandle.write( "PerformanceProfilerDir=%s\n" % dialog.performanceProfilerPath.value() )

    viewsToRender = []
    if dialog.chooseViewsToRender.value():
        for vk in dialog.viewToRenderKnobs:
            if vk[0].value():
                viewsToRender.append(vk[1])

    if len(viewsToRender) > 0:
        fileHandle.write( "Views=%s\n" % ','.join(viewsToRender) )
    else:
        fileHandle.write( "Views=\n" )

    fileHandle.write( "StackSize=%s\n" % dialog.stackSize.value() )

    fileHandle.close()
    
    # Update task progress
    progressTask.setMessage("Submitting Job %d to Deadline" % jobCount)
    progressTask.setProgress(30)
    
    # Submit the job to Deadline
    args = []
    args.append( jobInfoFile )
    args.append( pluginInfoFile )
    if dialog.submitScene.value():
        args.append( root.name() )
    
    tempResults = ""
    
    # Submit Job
    progressTask.setProgress(50)
    
    # If submitting multiple jobs, acquire the semaphore so that only one job is submitted at a time.
    if semaphore:
        semaphore.acquire()
        
    try:
        tempResults = CallDeadlineCommand( args )
    finally:
        # Release the semaphore if necessary.
        if semaphore:
            semaphore.release()
    
    # Update task progress
    progressTask.setMessage("Complete!")
    progressTask.setProgress(100)
    
    print "Job submission #%d complete" % jobCount
    
    # If submitting multiple jobs, just print the results to the console, otherwise show them to the user.
    if semaphore:
        print tempResults
    else:
        nuke.executeInMainThread( nuke.message, tempResults )
    
    print "------ Out SubmitJob ------"
    return tempResults


#This will recursively find nodes of the given class (used to find write nodes, even if they're embedded in groups).  
def RecursiveFindNodes(nodeClass, startNode):
    print "------ In RecursiveFindNodes ------"
    nodeList = []
    
    if startNode != None:
        if startNode.Class() == nodeClass:
            nodeList = [startNode]
        elif isinstance(startNode, nuke.Group):
            for child in startNode.nodes():
                nodeList.extend( RecursiveFindNodes(nodeClass, child) )
                
    print "------ Out RecursiveFindNodes ------"
    return nodeList

def getOutputType():
    writeNodes = RecursiveFindNodes( "Write", nuke.Root() )
    outputCount = 0
    for node in writeNodes:
        if 'Precomp' not in node.fullName():
            print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
            reading = False
            if node.knob( 'reading' ):
                reading = node.knob( 'reading' ).value()
                
            # Need at least one write node that is enabled, and not set to read in as well.
            if not node.knob( 'disable' ).value() and not reading:
                outputCount = outputCount + 1            
                filename = nuke.filename(node)            
                if filename == "":
                    fileExtension = ""
                else:
                    fileExtension = node.knob( 'file_type' ).value()
                
    return fileExtension.upper()

def getFrameSize():
    width = nuke.root().width()
    height = nuke.root().height()
    frameSize = str(width) + "x" + str(height)
    
    return frameSize
        
def getProjectPhase():
    path = nuke.Root()['name'].getValue()        
    pathInfo = path.split("/")    
    tmp = pathInfo[-3]        
    phaseInfo = tmp.split("_")
    showPhase = phaseInfo[-1]
    return showPhase.upper()

# The main submission function.
def SubmitToDeadline( currNukeScriptPath ):
    print "------ In SubmitToDeadline ------"
    global dialog
    global nukeScriptPath
    global deadlineHome
    
    
    # Add the current nuke script path to the system path.
    nukeScriptPath = currNukeScriptPath
    sys.path.append( nukeScriptPath )
    
    # VISMO_DeadlineGlobals contains initial values for the submission dialog. These can be modified
    # by an external sanity scheck script.
    import VISMO_DeadlineGlobals
    
    # Get the root node.
    root = nuke.Root()
    
    # If the Nuke script hasn't been saved, its name will be 'Root' instead of the file name.
    if root.name() == "Root":
        nuke.message( "The Nuke script must be saved before it can be submitted to Deadline." )
        return
    
    # If the Nuke script has been modified, then save it.
    if root.modified():
        nuke.scriptSave( root.name() )
    
    # Get the current user Deadline home directory, which we'll use to store settings and temp files.
    deadlineHome = CallDeadlineCommand( ["-GetCurrentUserHomeDirectory",] )
    
    deadlineHome = deadlineHome.replace( "\n", "" ).replace( "\r", "" )
    deadlineSettings = deadlineHome + "/settings"
    deadlineTemp = deadlineHome + "/temp"
    
    # Get the maximum priority.
    try:
        output = CallDeadlineCommand( ["-getmaximumpriority",] )
        maximumPriority = int(output)
    except:
        maximumPriority = 100
    
    # Get the pools.
    output = CallDeadlineCommand( ["-pools",] )
    pools = output.splitlines()
    
    secondaryPools = []
    secondaryPools.append(" ")
    for currPool in pools:
        secondaryPools.append(currPool)
    
    # Get the groups.
    output = CallDeadlineCommand( ["-groups",] )
    groups = output.splitlines()
    
    initFrameListMode = "Global"
    initCustomFrameList = None
    
    # Set initial settings for submission dialog.
    VISMO_DeadlineGlobals.initJobName = os.path.basename( nuke.Root().name() )
    VISMO_DeadlineGlobals.initComment = ""
    
    VISMO_DeadlineGlobals.initDepartment = ""
    
##################################################################
    VISMO_DeadlineGlobals.initProjectPhase = getProjectPhase()
    VISMO_DeadlineGlobals.initFrameSize = getFrameSize()
    VISMO_DeadlineGlobals.initFileType = getOutputType()
##################################################################
    
    VISMO_DeadlineGlobals.initPool = "none"
    VISMO_DeadlineGlobals.initSecondaryPool = " "
    VISMO_DeadlineGlobals.initGroup = "none"
    VISMO_DeadlineGlobals.initPriority = 50
    VISMO_DeadlineGlobals.initTaskTimeout = 0
    VISMO_DeadlineGlobals.initAutoTaskTimeout = False
    VISMO_DeadlineGlobals.initConcurrentTasks = 1
    VISMO_DeadlineGlobals.initLimitConcurrentTasks = True
    VISMO_DeadlineGlobals.initMachineLimit = 0
    VISMO_DeadlineGlobals.initIsBlacklist = False
    VISMO_DeadlineGlobals.initMachineList = ""
    VISMO_DeadlineGlobals.initLimitGroups = ""
    VISMO_DeadlineGlobals.initDependencies = ""
    VISMO_DeadlineGlobals.initOnComplete = "Nothing"
    VISMO_DeadlineGlobals.initSubmitSuspended = False
    VISMO_DeadlineGlobals.initChunkSize = 10
    VISMO_DeadlineGlobals.initThreads = 0
    VISMO_DeadlineGlobals.initMemoryUsage = 0
    VISMO_DeadlineGlobals.initSeparateJobs = False
    VISMO_DeadlineGlobals.initSeparateJobDependencies = False
    VISMO_DeadlineGlobals.initSeparateTasks = False
    VISMO_DeadlineGlobals.initUseNodeRange = True
    VISMO_DeadlineGlobals.initReadFileOnly = False
    VISMO_DeadlineGlobals.initSelectedOnly = False
    VISMO_DeadlineGlobals.initSubmitScene = False
    VISMO_DeadlineGlobals.initBatchMode = False
    VISMO_DeadlineGlobals.initContinueOnError = False
    VISMO_DeadlineGlobals.initUseGpu = False
    VISMO_DeadlineGlobals.initEnforceRenderOrder = False
    VISMO_DeadlineGlobals.initStackSize = 0
    VISMO_DeadlineGlobals.initProxyMode = False
    VISMO_DeadlineGlobals.initPerformanceProfiler = False
    VISMO_DeadlineGlobals.initPerformanceProfilerPath = ""

    VISMO_DeadlineGlobals.initUseNukeX = False
    if nuke.env[ 'nukex' ]:
        VISMO_DeadlineGlobals.initUseNukeX = True
        
    VISMO_DeadlineGlobals.initUseDraft = False
    VISMO_DeadlineGlobals.initDraftTemplate = ""
    VISMO_DeadlineGlobals.initDraftUser = ""
    VISMO_DeadlineGlobals.initDraftEntity = ""
    VISMO_DeadlineGlobals.initDraftVersion = ""
    VISMO_DeadlineGlobals.initDraftExtraArgs = ""
    VISMO_DeadlineGlobals.initProjectManagement = "Shotgun" #Default to Shotgun
    
    # Read In Sticky Settings
    configFile = deadlineSettings + "/nuke_py_submission.ini"
    print "Reading sticky settings from %s" % configFile
    try:
        if os.path.isfile( configFile ):
            config = ConfigParser.ConfigParser()
            config.read( configFile )
            
            if config.has_section( "Sticky" ):
                if config.has_option( "Sticky", "FrameListMode" ):
                    initFrameListMode = config.get( "Sticky", "FrameListMode" )
                if config.has_option( "Sticky", "CustomFrameList" ):
                    initCustomFrameList = config.get( "Sticky", "CustomFrameList" )
                
                if config.has_option( "Sticky", "Department" ):
                    VISMO_DeadlineGlobals.initDepartment = config.get( "Sticky", "Department" )
                if config.has_option( "Sticky", "Pool" ):
                    VISMO_DeadlineGlobals.initPool = config.get( "Sticky", "Pool" )
                if config.has_option( "Sticky", "SecondaryPool" ):
                    VISMO_DeadlineGlobals.initSecondaryPool = config.get( "Sticky", "SecondaryPool" )
                if config.has_option( "Sticky", "Group" ):
                    VISMO_DeadlineGlobals.initGroup = config.get( "Sticky", "Group" )
                if config.has_option( "Sticky", "Priority" ):
                    VISMO_DeadlineGlobals.initPriority = config.getint( "Sticky", "Priority" )
                if config.has_option( "Sticky", "MachineLimit" ):
                    VISMO_DeadlineGlobals.initMachineLimit = config.getint( "Sticky", "MachineLimit" )
                if config.has_option( "Sticky", "IsBlacklist" ):
                    VISMO_DeadlineGlobals.initIsBlacklist = config.getboolean( "Sticky", "IsBlacklist" )
                if config.has_option( "Sticky", "MachineList" ):
                    VISMO_DeadlineGlobals.initMachineList = config.get( "Sticky", "MachineList" )
                if config.has_option( "Sticky", "LimitGroups" ):
                    VISMO_DeadlineGlobals.initLimitGroups = config.get( "Sticky", "LimitGroups" )
                if config.has_option( "Sticky", "SubmitSuspended" ):
                    VISMO_DeadlineGlobals.initSubmitSuspended = config.getboolean( "Sticky", "SubmitSuspended" )
                if config.has_option( "Sticky", "ChunkSize" ):
                    VISMO_DeadlineGlobals.initChunkSize = config.getint( "Sticky", "ChunkSize" )
                if config.has_option( "Sticky", "ConcurrentTasks" ):
                    VISMO_DeadlineGlobals.initConcurrentTasks = config.getint( "Sticky", "ConcurrentTasks" )
                if config.has_option( "Sticky", "LimitConcurrentTasks" ):
                    VISMO_DeadlineGlobals.initLimitConcurrentTasks = config.getboolean( "Sticky", "LimitConcurrentTasks" )
                if config.has_option( "Sticky", "Threads" ):
                    VISMO_DeadlineGlobals.initThreads = config.getint( "Sticky", "Threads" )
                if config.has_option( "Sticky", "SubmitScene" ):
                    VISMO_DeadlineGlobals.initSubmitScene = config.getboolean( "Sticky", "SubmitScene" )
                if config.has_option( "Sticky", "BatchMode" ):
                    VISMO_DeadlineGlobals.initBatchMode = config.getboolean( "Sticky", "BatchMode" )
                if config.has_option( "Sticky", "ContinueOnError" ):
                    VISMO_DeadlineGlobals.initContinueOnError = config.getboolean( "Sticky", "ContinueOnError" )
                if config.has_option( "Sticky", "UseNodeRange" ):
                    VISMO_DeadlineGlobals.initUseNodeRange = config.getboolean( "Sticky", "UseNodeRange" )
                if config.has_option( "Sticky", "UseGpu" ):
                    VISMO_DeadlineGlobals.initUseGpu = config.getboolean( "Sticky", "UseGpu" )
                if config.has_option( "Sticky", "EnforceRenderOrder" ):
                    VISMO_DeadlineGlobals.initEnforceRenderOrder = config.getboolean( "Sticky", "EnforceRenderOrder" )
                if config.has_option( "Sticky", "ProxyMode" ):
                    VISMO_DeadlineGlobals.initProxyMode = config.getboolean( "Sticky", "ProxyMode" )
                if config.has_option( "Sticky", "PerformanceProfiler" ):
                    VISMO_DeadlineGlobals.initPerformanceProfiler = config.getboolean( "Sticky", "PerformanceProfiler")
                if config.has_option( "Sticky", "PerformanceProfilerPath" ):
                    VISMO_DeadlineGlobals.initPerformanceProfilerPath = config.get( "Sticky", "PerformanceProfilerPath" )
                if config.has_option( "Sticky", "UseDraft" ):
                    VISMO_DeadlineGlobals.initUseDraft = config.getboolean( "Sticky", "UseDraft" )
                if config.has_option( "Sticky", "DraftTemplate" ):
                    VISMO_DeadlineGlobals.initDraftTemplate = config.get( "Sticky", "DraftTemplate" )
                if config.has_option( "Sticky", "DraftUser" ):
                    VISMO_DeadlineGlobals.initDraftUser = config.get( "Sticky", "DraftUser" )
                if config.has_option( "Sticky", "DraftEntity" ):
                    VISMO_DeadlineGlobals.initDraftEntity = config.get( "Sticky", "DraftEntity" )
                if config.has_option( "Sticky", "DraftVersion" ):
                    VISMO_DeadlineGlobals.initDraftVersion = config.get( "Sticky", "DraftVersion" )
                if config.has_option( "Sticky", "DraftExtraArgs"):
                    VISMO_DeadlineGlobals.initDraftExtraArgs = config.get( "Sticky", "DraftExtraArgs" )
                if config.has_option( "Sticky", "ProjectManagement" ):
                    VISMO_DeadlineGlobals.initProjectManagement = config.get( "Sticky", "ProjectManagement" )
    except:
        print( "Could not read sticky settings")
        print traceback.format_exc()
    
    shotgunKVPs = {}
    ftrackKVPs = {}
    
    try:
                root = nuke.Root()
                if "FrameListMode" in root.knobs():
                    initFrameListMode = ( root.knob( "FrameListMode" ) ).value() 
                    
                if "CustomFrameList" in root.knobs():
                    initCustomFrameList = ( root.knob( "CustomFrameList" ) ).value() 
                    
                if "Department" in root.knobs():
                    VISMO_DeadlineGlobals.initDepartment = ( root.knob( "Department" ) ).value()
                    
                if "Pool" in root.knobs():
                    VISMO_DeadlineGlobals.initPool = ( root.knob( "Pool" ) ).value()
                    
                if "SecondaryPool" in root.knobs():
                    VISMO_DeadlineGlobals.initSecondaryPool = ( root.knob( "SecondaryPool" ) ).value()
                    
                if "Group" in root.knobs():
                    VISMO_DeadlineGlobals.initGroup = ( root.knob( "Group" ) ).value()
                    
                if "Priority" in root.knobs():
                    VISMO_DeadlineGlobals.initPriority = int( ( root.knob( "Priority" ) ).value() )
                    
                if "MachineLimit" in root.knobs():
                    VISMO_DeadlineGlobals.initMachineLimit = int( ( root.knob( "MachineLimit" ) ).value() )
                    
                if "IsBlacklist" in root.knobs():
                    VISMO_DeadlineGlobals.initIsBlacklist = StrToBool( ( root.knob( "IsBlacklist" ) ).value() )
                
                if "MachineList" in root.knobs():
                    VISMO_DeadlineGlobals.initMachineList = ( root.knob( "MachineList" ) ).value()
                
                if "LimitGroups" in root.knobs():
                    VISMO_DeadlineGlobals.initLimitGroups = ( root.knob( "LimitGroups" ) ).value()
                
                if "SubmitSuspended" in root.knobs():
                    VISMO_DeadlineGlobals.initSubmitSuspended = StrToBool( ( root.knob( "SubmitSuspended" ) ).value() )
                
                if "ChunkSize" in root.knobs():
                    VISMO_DeadlineGlobals.initChunkSize = int( ( root.knob( "ChunkSize" ) ).value() )
                
                if "ConcurrentTasks" in root.knobs():
                    VISMO_DeadlineGlobals.initConcurrentTasks = int( ( root.knob( "ConcurrentTasks" ) ).value() )
                
                if "LimitConcurrentTasks" in root.knobs():
                    VISMO_DeadlineGlobals.initLimitConcurrentTasks = StrToBool( ( root.knob( "LimitConcurrentTasks" ) ).value() )
                
                if "Threads" in root.knobs():
                    VISMO_DeadlineGlobals.initThreads = int( ( root.knob( "Threads" ) ).value() )
                
                if "SubmitScene" in root.knobs():
                    VISMO_DeadlineGlobals.initSubmitScene = StrToBool( ( root.knob( "SubmitScene" ) ).value() )
                
                if "BatchMode" in root.knobs():
                    VISMO_DeadlineGlobals.initBatchMode = StrToBool( ( root.knob( "BatchMode" ) ).value() )
                
                if "ContinueOnError" in root.knobs():
                    VISMO_DeadlineGlobals.initContinueOnError = StrToBool( ( root.knob( "ContinueOnError" ) ).value() )
                
                if "UseNodeRange" in root.knobs():
                    VISMO_DeadlineGlobals.initUseNodeRange = StrToBool( ( root.knob( "UseNodeRange" ) ).value() )
                
                if "UseGpu" in root.knobs():
                    VISMO_DeadlineGlobals.initUseGpu = StrToBool( ( root.knob( "UseGpu" ) ).value() )
                    
                if "EnforceRenderOrder" in root.knobs():
                    VISMO_DeadlineGlobals.initEnforceRenderOrder = StrToBool( ( root.knob( "EnforceRenderOrder" ) ).value() )

                if "ProxyMode" in root.knobs():
                    VISMO_DeadlineGlobals.initProxyMode = StrToBool( ( root.knob( "ProxyMode" ) ).value() )

                if "PerformanceProfiler" in root.knobs():
                    VISMO_DeadlineGlobals.initPerformanceProfiler = StrToBool( ( root.knob( "PerformanceProfiler" ) ).value() )

                if "PerformanceProfilerPath" in root.knobs():
                    VISMO_DeadlineGlobals.initPerformanceProfilerPath = ( root.knob( "PerformanceProfilerPath" ) ).value()

                if "UseDraft" in root.knobs():
                    VISMO_DeadlineGlobals.initUseDraft = StrToBool( ( root.knob( "UseDraft" ) ).value() )
                
                if "DraftTemplate" in root.knobs():
                    VISMO_DeadlineGlobals.initDraftTemplate = ( root.knob( "DraftTemplate" ) ).value()
                
                if "DraftUser" in root.knobs():
                    VISMO_DeadlineGlobals.initDraftUser = ( root.knob( "DraftUser" ) ).value()
                
                if "DraftEntity" in root.knobs():
                    VISMO_DeadlineGlobals.initDraftEntity = ( root.knob( "DraftEntity" ) ).value()
                
                if "DraftVersion" in root.knobs():
                    VISMO_DeadlineGlobals.initDraftVersion = ( root.knob( "DraftVersion" ) ).value()
                    
                if "DraftExtraArgs" in root.knobs():
                    VISMO_DeadlineGlobals.initDraftExtraArgs = ( root.knob( "DraftExtraArgs" ) ).value()

                if "ProjectManagement" in root.knobs():
                    VISMO_DeadlineGlobals.initProjectManagement = ( root.knob( "ProjectManagement" ) ).value()

                if "DeadlineSGData" in root.knobs():
                    sgDataKnob = root.knob( "DeadlineSGData" )
                    shotgunKVPs = ast.literal_eval( sgDataKnob.toScript() )

                if "DeadlineFTData" in root.knobs():
                    ftDataKnob = root.knob( "DeadlineFTData" )
                    ftrackKVPs = ast.literal_eval( ftDataKnob.toScript() )
                
    except:
        print "Could not read knob settings."
        print traceback.format_exc()
    
    if initFrameListMode != "Custom":
        startFrame = nuke.Root().firstFrame()
        endFrame = nuke.Root().lastFrame()
        if initFrameListMode == "Input":
            try:
                activeInput = nuke.activeViewer().activeInput()
                startFrame = nuke.activeViewer().node().input(activeInput).frameRange().first()
                endFrame = nuke.activeViewer().node().input(activeInput).frameRange().last()
            except:
                pass
        
        if startFrame == endFrame:
            VISMO_DeadlineGlobals.initFrameList = str(startFrame)
        else:
            VISMO_DeadlineGlobals.initFrameList = str(startFrame) + "-" + str(endFrame)
    else:
        if initCustomFrameList == None or initCustomFrameList.strip() == "":
            startFrame = nuke.Root().firstFrame()
            endFrame = nuke.Root().lastFrame()
            if startFrame == endFrame:
                VISMO_DeadlineGlobals.initFrameList = str(startFrame)
            else:
                VISMO_DeadlineGlobals.initFrameList = str(startFrame) + "-" + str(endFrame)
        else:
            VISMO_DeadlineGlobals.initFrameList = initCustomFrameList.strip()
 
###    
    # Run the sanity check script if it exists, which can be used to set some initial values.
    sanityCheckFile = nukeScriptPath + "/CustomSanityChecks.py"
    if os.path.isfile( sanityCheckFile ):
        print( "Running sanity check script: " + sanityCheckFile )
        try:
            import CustomSanityChecks
            sanityResult = CustomSanityChecks.RunSanityCheck()
            if not sanityResult:
                print( "Sanity check returned false, exiting" )
                return
        except:
            print( "Could not run CustomSanityChecks.py script" )
            print( traceback.format_exc() )
    
    if VISMO_DeadlineGlobals.initPriority > maximumPriority:
        VISMO_DeadlineGlobals.initPriority = (maximumPriority / 2)
    
    # Both of these can't be enabled!
    if VISMO_DeadlineGlobals.initSeparateJobs and VISMO_DeadlineGlobals.initSeparateTasks:
        VISMO_DeadlineGlobals.initSeparateTasks = False
###

### 
    # Check for potential issues and warn user about any that are found.
    warningMessages = ""
    writeNodes = RecursiveFindNodes( "Write", nuke.Root() )
    deepWriteNodes = RecursiveFindNodes( "DeepWrite", nuke.Root() )
    writeGeoNodes = RecursiveFindNodes( "WriteGeo", nuke.Root() )
    
    writeNodes.extend(deepWriteNodes)
    writeNodes.extend(writeGeoNodes)

    print "Found a total of %d write nodes" % len( writeNodes )

    # Check all the output filenames if they are local or not padded (non-movie files only).
    outputCount = 0
    for node in writeNodes:
        if 'Precomp' not in node.fullName():
            print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
            reading = False
            if node.knob( 'reading' ):
                reading = node.knob( 'reading' ).value()
            
            # Need at least one write node that is enabled, and not set to read in as well.
            if not node.knob( 'disable' ).value() and not reading:
                outputCount = outputCount + 1
                
                # if root.proxy() and node.knob( 'proxy' ).value() != "":
                    # filename = node.knob( 'proxy' ).value()
                # else:
                    # filename = node.knob( 'file' ).value()
                    
                filename = nuke.filename(node)
    
                if filename == "":
                    warningMessages = warningMessages + "No output path for write node '" + node.name() + "' is defined\n\n"
                else:
                    fileExtension = node.knob( 'file_type' ).value()
                    
                    if filename == None or filename == "":
                        warningMessages = warningMessages + "Output path for write node '" + node.name() + "' is empty\n\n"
                    else:
                        if IsPathLocal( filename ):
                            warningMessages = warningMessages + "Output path for write node '" + node.name() + "' is local:\n" + filename + "\n\n"
                        if not HasExtension( filename ) and fileExtension.strip() == "":
                            warningMessages = warningMessages + "Output path for write node '%s' has no extension:\n%s\n\n"  % (node.name(), filename)
                        if not IsMovie( filename ) and not IsPadded( os.path.basename( filename ) ):
                            warningMessages = warningMessages + "Output path for write node '" + node.name() + "' is not padded:\n" + filename + "\n\n"
    
    # Warn if there are no write nodes.
    if outputCount == 0:
        warningMessages = warningMessages + "At least one enabled write node that has 'read file' disabled is required to render\n\n"
    
    if len(nuke.views())  == 0:
        warningMessages = warningMessages + "At least one view is required to render\n\n"
    
    # If there are any warning messages, show them to the user.
    if warningMessages != "":
        warningMessages = warningMessages + "Do you still wish to submit this job to Deadline?"
        answer = nuke.ask( warningMessages )
        if not answer:
            return
###

    
    print "Creating submission dialog..."
    
    # Create an instance of the submission dialog.
    dialog = DeadlineDialog( maximumPriority, pools, secondaryPools, groups )
    
    # Set the initial values.
    dialog.jobName.setValue( VISMO_DeadlineGlobals.initJobName )
    dialog.comment.setValue( VISMO_DeadlineGlobals.initComment )
    dialog.department.setValue( VISMO_DeadlineGlobals.initDepartment )
    
    dialog.projectPhase.setValue( VISMO_DeadlineGlobals.initProjectPhase )
    dialog.frameSize.setValue( VISMO_DeadlineGlobals.initFrameSize )
    dialog.fileType.setValue( VISMO_DeadlineGlobals.initFileType )
    
    dialog.pool.setValue( VISMO_DeadlineGlobals.initPool )
    dialog.secondaryPool.setValue( VISMO_DeadlineGlobals.initSecondaryPool )
    dialog.group.setValue( VISMO_DeadlineGlobals.initGroup )
    dialog.priority.setValue( VISMO_DeadlineGlobals.initPriority )
    dialog.taskTimeout.setValue( VISMO_DeadlineGlobals.initTaskTimeout )
    dialog.autoTaskTimeout.setValue( VISMO_DeadlineGlobals.initAutoTaskTimeout )
    dialog.concurrentTasks.setValue( VISMO_DeadlineGlobals.initConcurrentTasks )
    dialog.limitConcurrentTasks.setValue( VISMO_DeadlineGlobals.initLimitConcurrentTasks )
    dialog.machineLimit.setValue( VISMO_DeadlineGlobals.initMachineLimit )
    dialog.isBlacklist.setValue( VISMO_DeadlineGlobals.initIsBlacklist )
    dialog.machineList.setValue( VISMO_DeadlineGlobals.initMachineList )
    dialog.limitGroups.setValue( VISMO_DeadlineGlobals.initLimitGroups )
    dialog.dependencies.setValue( VISMO_DeadlineGlobals.initDependencies )
    dialog.onComplete.setValue( VISMO_DeadlineGlobals.initOnComplete )
    dialog.submitSuspended.setValue( VISMO_DeadlineGlobals.initSubmitSuspended )
    
    dialog.frameListMode.setValue( initFrameListMode )
    dialog.frameList.setValue( VISMO_DeadlineGlobals.initFrameList )
    dialog.chunkSize.setValue( VISMO_DeadlineGlobals.initChunkSize )
    dialog.threads.setValue( VISMO_DeadlineGlobals.initThreads )
    dialog.memoryUsage.setValue( VISMO_DeadlineGlobals.initMemoryUsage )
    dialog.separateJobs.setValue( VISMO_DeadlineGlobals.initSeparateJobs )
    dialog.separateJobDependencies.setValue( VISMO_DeadlineGlobals.initSeparateJobDependencies )
    dialog.separateTasks.setValue( VISMO_DeadlineGlobals.initSeparateTasks )
    dialog.readFileOnly.setValue( VISMO_DeadlineGlobals.initReadFileOnly )
    dialog.selectedOnly.setValue( VISMO_DeadlineGlobals.initSelectedOnly )
    dialog.submitScene.setValue( VISMO_DeadlineGlobals.initSubmitScene )
    dialog.useNukeX.setValue( VISMO_DeadlineGlobals.initUseNukeX )
    dialog.continueOnError.setValue( VISMO_DeadlineGlobals.initContinueOnError )
    dialog.batchMode.setValue( VISMO_DeadlineGlobals.initBatchMode )
    dialog.useNodeRange.setValue( VISMO_DeadlineGlobals.initUseNodeRange )
    dialog.useGpu.setValue( VISMO_DeadlineGlobals.initUseGpu )
    dialog.enforceRenderOrder.setValue( VISMO_DeadlineGlobals.initEnforceRenderOrder )
    dialog.proxyMode.setValue( VISMO_DeadlineGlobals.initProxyMode )
    dialog.performanceProfiler.setValue( VISMO_DeadlineGlobals.initPerformanceProfiler )
    dialog.performanceProfilerPath.setValue( VISMO_DeadlineGlobals.initPerformanceProfilerPath )
    #dialog.viewsToRender.setValue( VISMO_DeadlineGlobals.initViews )
    dialog.stackSize.setValue( VISMO_DeadlineGlobals.initStackSize )
    
    dialog.separateJobs.setEnabled( len( writeNodes ) > 0 )
    dialog.separateTasks.setEnabled( len( writeNodes ) > 0 )
    
    dialog.separateJobDependencies.setEnabled( dialog.separateJobs.value() )
    dialog.useNodeRange.setEnabled( dialog.separateJobs.value() or dialog.separateTasks.value() )
    dialog.frameList.setEnabled( not (dialog.separateJobs.value() and dialog.useNodeRange.value()) and not dialog.separateTasks.value() )
    
    dialog.submitDraftJob.setValue( VISMO_DeadlineGlobals.initUseDraft )
    dialog.templatePath.setValue( VISMO_DeadlineGlobals.initDraftTemplate )
    dialog.draftUser.setValue( VISMO_DeadlineGlobals.initDraftUser )
    dialog.draftEntity.setValue( VISMO_DeadlineGlobals.initDraftEntity )
    dialog.draftVersion.setValue( VISMO_DeadlineGlobals.initDraftVersion )
    dialog.draftExtraArgs.setValue( VISMO_DeadlineGlobals.initDraftExtraArgs )
    
    dialog.templatePath.setEnabled( dialog.submitDraftJob.value() )
    dialog.draftUser.setEnabled( dialog.submitDraftJob.value() )
    dialog.draftEntity.setEnabled( dialog.submitDraftJob.value() )
    dialog.draftVersion.setEnabled( dialog.submitDraftJob.value() )
    dialog.draftExtraArgs.setEnabled( dialog.submitDraftJob.value() )

    dialog.shotgunKVPs = shotgunKVPs
    dialog.ftrackKVPs = ftrackKVPs

    dialog.projectManagementCombo.setValue( VISMO_DeadlineGlobals.initProjectManagement )
    ChangeProjectManager( VISMO_DeadlineGlobals.initProjectManagement )
    
    # Show the dialog.
    success = False
    while not success:
        success = dialog.ShowDialog()
        if not success:
            WriteStickySettings( dialog, configFile )
            return
        
        errorMessages = ""
        warningMessages = ""
        
        # Check that frame range is valid.
        if dialog.frameList.value().strip() == "":
            errorMessages = errorMessages + "No frame list has been specified.\n\n"
        
        # If submitting separate write nodes, make sure there are jobs to submit
        if dialog.readFileOnly.value() or dialog.selectedOnly.value():
            validNodeFound = False
            for node in writeNodes:
                if 'Precomp' not in node.fullName():
                    print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                    if not node.knob( 'disable' ).value():
                        validNodeFound = True
                        if dialog.readFileOnly.value():
                            if node.knob( 'reading' ) and not node.knob( 'reading' ).value():
                                validNodeFound = False
                        if dialog.selectedOnly.value() and not node.isSelected():
                            validNodeFound = False
                        
                        if validNodeFound:
                            break
                    
            if not validNodeFound:
                if dialog.readFileOnly.value() and dialog.selectedOnly.value():
                    errorMessages = errorMessages + "There are no selected write nodes with 'Read File' enabled, so there are no jobs to submit.\n\n"
                elif dialog.readFileOnly.value():
                    errorMessages = errorMessages + "There are no write nodes with 'Read File' enabled, so there are no jobs to submit.\n\n"
                elif dialog.selectedOnly.value():
                    errorMessages = errorMessages + "There are no selected write nodes, so there are no jobs to submit.\n\n"
        
        # Check if at least one view has been selected.
        if dialog.chooseViewsToRender.value():
            viewCount = 0
            for vk in dialog.viewToRenderKnobs:
                if vk[0].value():
                    viewCount = viewCount + 1
                    
            if viewCount == 0:
                errorMessages = errorMessages + "There are no views selected.\n\n"
        
        # Check if proxy mode is enabled and Render using Proxy Mode is disabled, then warn the user.
        if root.proxy() and not dialog.proxyMode.value():
            warningMessages = warningMessages + "Proxy Mode is enabled and Render using Proxy Mode is disabled, which may cause problems when rendering through Deadline.\n\n"
        
        # Check if the script file is local and not being submitted to Deadline.
        if not dialog.submitScene.value():
            if IsPathLocal( root.name() ):
                warningMessages = warningMessages + "Nuke script path is local and is not being submitted to Deadline:\n" + root.name() + "\n\n"

        # Check Performance Profile Path
        if dialog.performanceProfiler.value():
            if not os.path.exists( dialog.performanceProfilerPath.value() ):
                errorMessages += "Performance Profiler is enabled, but an XML directory has not been selected (or it does not exist). Either select a valid network path, or disable Performance Profiling.\n\n"
        
        # Check Draft template path
        if dialog.submitDraftJob.value():
            if not os.path.exists( dialog.templatePath.value() ):
                errorMessages += "Draft job submission is enabled, but a Draft template has not been selected (or it does not exist). Either select a valid template, or disable Draft job submission.\n\n"
        
        if dialog.separateTasks.value() and dialog.frameListMode.value() == "Custom" and not dialog.useNodeRange.value():
            errorMessages += "Custom frame list is not supported when submitting write nodes as separate tasks. Please choose Global or Input, or enable Use Node's Frame List.\n\n"
        
        # Alert the user of any errors.
        if errorMessages != "":
            errorMessages = errorMessages + "Please fix these issues and submit again."
            nuke.message( errorMessages )
            success = False
        
        # Alert the user of any warnings.
        if success and warningMessages != "":
            warningMessages = warningMessages + "Do you still wish to submit this job to Deadline?"
            answer = nuke.ask( warningMessages )
            if not answer:
                WriteStickySettings( dialog, configFile )
                print "------ Out SubmitToDeadline 6 ------"
                return
    
    # Save sticky settings
    WriteStickySettings( dialog, configFile )
#########################################################
    print "#########################################################"
    tempJobName = dialog.jobName.value()
    print "Job name: " + tempJobName    
    tempJobName = tempJobName[:-3]
    print "Job name: " + tempJobName
    tempDependencies = dialog.dependencies.value()
    tempFrameList = dialog.frameList.value().strip()
    tempChunkSize = dialog.chunkSize.value()
    tempIsMovie = False
    
    # Check if we should be submitting a separate job for each write node.
    if dialog.separateJobs.value():
        jobCount = 0
        previousJobId = ""
        submitThreads = []
        semaphore = threading.Semaphore()
        
        writeNodes = sorted( writeNodes, key = lambda node: node['render_order'].value() )
        
        for node in writeNodes:
            if 'Precomp' not in node.fullName():
                print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                print "Now processing %s" % node.name()
                #increment job count -- will be used so not all submissions try to write to the same .job files simultaneously
                jobCount += 1
                    
                # Check if we should enter the loop for this node.
                enterLoop = False
                if not node.knob( 'disable' ).value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and node.knob( 'reading' ):
                        enterLoop = enterLoop and node.knob( 'reading' ).value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and node.isSelected()
                
                if enterLoop:
                    tempJobName = dialog.jobName.value() + " - " + node.name()
                    print "Job name: " + tempJobName
                    tempJobName = tempJobName[:-3]
                    print "Job name: " + tempJobName
                    
                    # Check if the write node is overriding the frame range
                    if dialog.useNodeRange.value() and node.knob( 'use_limit' ).value():
                        tempFrameList = str(int(node.knob('first').value())) + "-" + str(int(node.knob('last').value()))
                    else:
                        tempFrameList = dialog.frameList.value().strip()
                    
                    if IsMovie( node.knob( 'file' ).value() ):
                        tempChunkSize = 1000000
                        tempIsMovie = True
                    else:
                        tempChunkSize = dialog.chunkSize.value()
                        tempIsMovie = False
                    
                    #if creating sequential dependencies, parse for JobId to be used for the next Job's dependencies
                    if dialog.separateJobDependencies.value():
                        if jobCount > 1 and not tempDependencies == "":
                            tempDependencies = tempDependencies + "," + previousJobId
                        elif tempDependencies == "":
                            tempDependencies = previousJobId
                            
                        submitJobResults = SubmitJob( dialog, root, node, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, jobCount, semaphore )                         
                        for line in submitJobResults.splitlines():
                            if line.startswith("JobID="):
                                previousJobId = line[6:]
                                break
                        tempDependencies = dialog.dependencies.value() #reset dependencies
                    else: #Create a new thread to do the submission
                        print "Spawning submission thread #%d..." % jobCount
                        submitThread = threading.Thread( None, SubmitJob, args = ( dialog, root, node, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, jobCount, semaphore ) )
                        submitThread.start()
                        submitThreads.append( submitThread )
        
        if not dialog.separateJobDependencies.value():
            print "Spawning results thread..."
            resultsThread = threading.Thread( None, WaitForSubmissions, args = ( submitThreads, ) )
            resultsThread.start()
            
    elif dialog.separateTasks.value():
        #Create a new thread to do the submission
        print "Spawning submission thread..."
        submitThread = threading.Thread( None, SubmitJob, None, ( dialog, root, None, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, 1, None ) )
        submitThread.start()
    else:
        for tempNode in writeNodes:
            if 'Precomp' not in tempNode.fullName():
                print '^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ TESTING ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^'
                if not tempNode.knob( 'disable' ).value():
                    enterLoop = True
                    if dialog.readFileOnly.value() and tempNode.knob( 'reading' ):
                        enterLoop = enterLoop and tempNode.knob( 'reading' ).value()
                    if dialog.selectedOnly.value():
                        enterLoop = enterLoop and tempNode.isSelected()
                    
                    if enterLoop:
                        if IsMovie( tempNode.knob( 'file' ).value() ):
                            tempChunkSize = 1000000
                            tempIsMovie = True
                            break
        
        #Create a new thread to do the submission
        print "Spawning submission thread..."
        submitThread = threading.Thread( None, SubmitJob, None, ( dialog, root, None, writeNodes, deadlineTemp, tempJobName, tempFrameList, tempDependencies, tempChunkSize, tempIsMovie, 1, None ) )
        submitThread.start()  
    
    print "Main Deadline thread exiting"
    print "------ Out SubmitToDeadline ------"

def WaitForSubmissions( submitThreads ):
    print "------ In WaitForSubmissions ------"
    for thread in submitThreads:
        thread.join()
    
    results = "Job submission complete. See the Script Editor output window for more information."
    nuke.executeInMainThread( nuke.message, results )
    
    print "Results thread exiting"
    print "------ Out WaitForSubmissions ------"

def GetRepositoryRoot():
    print "------ In GetRepositoryRoot ------"
    # On OSX, we look for the DEADLINE_PATH file. On other platforms, we use the environment variable.
    if os.path.exists( "/Users/Shared/Thinkbox/DEADLINE_PATH" ):
        with open( "/Users/Shared/Thinkbox/DEADLINE_PATH" ) as f: deadlineBin = f.read().strip()
        deadlineCommand = deadlineBin + "/deadlinecommand"
    else:
        try:
            deadlineBin = os.environ['DEADLINE_PATH']
        except KeyError:
            return ""
            
        if os.name == 'nt':
            deadlineCommand = deadlineBin + "\\deadlinecommand.exe"
        else:
            deadlineCommand = deadlineBin + "/deadlinecommand"
    
    startupinfo = None
    if os.name == 'nt' and hasattr( subprocess, 'STARTF_USESHOWWINDOW' ):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    proc = subprocess.Popen([deadlineCommand, "-root"], cwd=deadlineBin, stdout=subprocess.PIPE, startupinfo=startupinfo)
    
    root = proc.stdout.read()
    root = root.replace("\n","").replace("\r","")
    print "------ Out GetRepositoryRoot ------"
    return root

################################################################################
## DEBUGGING
################################################################################

#~ # Get the repository root
#~ path = GetRepositoryRoot()
#~ if path != "":
    #~ path += "/submission/Nuke/Main"
    #~ path = path.replace( "\\", "/" )
  
    #~ # Add the path to the system path
    #~ if path not in sys.path :
        #~ print "Appending \"" + path + "\" to system path to import SubmitNukeToDeadline module"
        #~ sys.path.append( path )
      
    #~ # Call the main function to begin job submission.
    #~ SubmitToDeadline( path )
#~ else:
    #~ nuke.message( "The SubmitNukeToDeadline.py script could not be found in the Deadline Repository. Please make sure that the Deadline Client has been installed on this machine, that the Deadline Client bin folder is set in the DEADLINE_PATH environment variable, and that the Deadline Client has been configured to point to a valid Repository." )