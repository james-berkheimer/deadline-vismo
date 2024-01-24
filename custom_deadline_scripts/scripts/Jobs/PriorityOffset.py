
#Imports
from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


#a global variable to hold the UI.
scriptDialog = None

def __main__( *args ):
    global scriptDialog
    
    #define the max value that the Range controls can go to.
    maximumPriority = RepositoryUtils.GetMaximumPriority()
    
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetSize( 350, 100 )
    scriptDialog.AllowResizingDialog( True )
    scriptDialog.SetTitle( "Set/Offset Priority of Selected Jobs" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "AbsLabel", "LabelControl", "Absolute Priority:", 0, 0 , "The absolute priority.", False )
    scriptDialog.AddRangeControlToGrid( "AbsBox", "RangeControl", 0, 0, maximumPriority, 0, 1, 0, 1 )
    absButton = scriptDialog.AddControlToGrid( "AbsButton", "ButtonControl", "Apply", 0, 2, expand=False )
    absButton.ValueModified.connect(AbsButtonPressed)
    
    scriptDialog.AddControlToGrid( "OffsetLabel", "LabelControl", "Priority Offset:", 1, 0 , "The priority offset.", False )
    scriptDialog.AddRangeControlToGrid( "OffsetBox", "RangeControl", 0, -maximumPriority, maximumPriority, 0, 1, 1, 1 )
    offsetButton = scriptDialog.AddControlToGrid( "OffsetButton", "ButtonControl", "Apply", 1, 2, expand=False )
    offsetButton.ValueModified.connect(OffsetButtonPressed)
    
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 2, 2, expand=False )
    closeButton.ValueModified.connect(CloseButtonPressed)
    
    scriptDialog.EndGrid()
    
    scriptDialog.ShowDialog( False )
    
def AbsButtonPressed( *args ):
    global scriptDialog
    jobs = MonitorUtils.GetSelectedJobs()
    priority = int( scriptDialog.GetValue( "AbsBox" ) )
    
    for job in jobs:
        job.JobPriority = priority
        print "Changed Priority of Job "+job.JobId+" to " +str(priority)
        print "Changed Priority of Job "+job.JobName+" to " +str(priority)
        RepositoryUtils.SaveJob(job)
        
        
def OffsetButtonPressed( *args ):
    global scriptDialog
    
    jobs = MonitorUtils.GetSelectedJobs()
    maximumPriority = RepositoryUtils.GetMaximumPriority()
    offset = int( scriptDialog.GetValue( "OffsetBox" ) )
    
    for job in jobs:
        priority = job.JobPriority + offset
        if priority > maximumPriority:
            priority = maximumPriority
        elif priority < 0:
            priority = 0
            
    job.JobPriority = priority
    print "Changed Priority of Job "+job.JobId+" to " +str(priority)
    print "Changed Priority of Job "+job.JobName+" to " +str(priority)
    RepositoryUtils.SaveJob(job)
    
    
def CloseButtonPressed( *args ):
    global scriptDialog
    scriptDialog.CloseDialog()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    