#Imports
import os
import string
from Deadline.Scripting import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog

########################################################################
## Globals
########################################################################
scriptDialog = None
selectedSlave = None

def __main__():
    global scriptDialog
    global selectedSlave
    global slaveGroups
    global slaveDescription
    global slaveComment
    
    selectedSlave = MonitorUtils.GetSelectedSlaveNames()
    slave_settings = RepositoryUtils.GetSlaveSettings(selectedSlave[0], True)
    slaveGroups = [str(thing) for thing in slave_settings.SlaveGroups]
    slaveDescription = slave_settings.SlaveDescription
    slaveComment = slave_settings.SlaveComment
        
    scriptDialog = DeadlineScriptDialog()
    scriptDialog.SetSize( 350, 100 )
    scriptDialog.AllowResizingDialog( True )
    scriptDialog.SetTitle( selectedSlave[0] + " - Slave Instance Manager" )
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Spawn Slave Instances", 0, 0, colSpan=2 )
    scriptDialog.AddControlToGrid( "SpawnLabel", "LabelControl", "Slave Instances:", 1, 0 , "How many instances to spawn from this slave.", False )
    scriptDialog.AddRangeControlToGrid( "InstancesBox", "RangeControl", 0, 0, 10, 0, 1, 1, 1 )
    spawnButton = scriptDialog.AddControlToGrid( "spawnButton", "ButtonControl", "Spawn", 1, 2, expand=False )
    spawnButton.ValueModified.connect(SpawnInstances)
    scriptDialog.AddControlToGrid( "SpacerLabel", "LabelControl", "", 2, 0 , "", False )
    scriptDialog.EndGrid()
    
    scriptDialog.AddGrid()
    scriptDialog.AddControlToGrid( "Separator1", "SeparatorControl", "Kill Slave Instances", 0, 0, colSpan=2 )
    scriptDialog.AddControlToGrid( "InstancesLabel", "LabelControl", "Existing Instances:", 1, 0 , "The number of instances already on this slave.", False )
    scriptDialog.AddControlToGrid( "ReadOnlyText", "ReadOnlyTextControl", len(GetSlaveIni().values()[0])-1, 1, 1 , "ReadOnlyTextControl", True, rowSpan=1, colSpan=1 )
    cleanButton = scriptDialog.AddControlToGrid( "CleanButton", "ButtonControl", "Clean", 1, 2, expand=False )
    cleanButton.ValueModified.connect(CleanSlaveInstances)
    scriptDialog.AddControlToGrid( "SpacerLabel", "LabelControl", "", 2, 0 , "", False )
    closeButton = scriptDialog.AddControlToGrid( "CloseButton", "ButtonControl", "Close", 3, 2, expand=False )
    closeButton.ValueModified.connect(CloseButtonPressed)
    scriptDialog.EndGrid()
    
    scriptDialog.ShowDialog( False )    
    
def CloseButtonPressed( *args ):
    global scriptDialog
    scriptDialog.CloseDialog()
    
def GetSlaveIni():
    global selectedSlave
    slaveInidir = {}
    pathToSlaveDir = "\c$\ProgramData\Thinkbox\Deadline9\slaves\\"
    slavesPath = "\\\\" + selectedSlave[0] + pathToSlaveDir
    slaveInidir[slavesPath] = os.listdir(slavesPath)
    return slaveInidir

def CheckForSlaveInstances():
    if GetSlaveIni():
        return True
    else:
        return False
    
def CleanSlaveInstances():
    #===============================================
    # Force stop and delete slave instances
    #===============================================
    for i in range(len(GetSlaveIni().values()[0])-1):        
        slaveInstanceName = str(selectedSlave[0] + '-' + string.ascii_uppercase[i])
        print (selectedSlave[0] + '-' + string.ascii_uppercase[i])
        # Stop
        print ("Shutting down: %s " % (slaveInstanceName), SlaveUtils.SendRemoteCommandWithResults(str(selectedSlave[0]), "ForceStopSlave"))
        # Delete
        RepositoryUtils.DeleteSlave(slaveInstanceName)        
        
    #===============================================
    # Get .ini files from slave.
    #===============================================
    for ini in GetSlaveIni().values()[0]:
        if ini != ".ini":
            print ("Deleting: " + GetSlaveIni().keys()[0] + "\\" + ini)
            os.remove(GetSlaveIni().keys()[0] + ini)
        
    #===============================================
    #Relaunch Host Slave
    #===============================================    
    SlaveUtils.SendRemoteCommand( str(selectedSlave[0]), "LaunchSlave")
            
def SpawnInstances():
    global scriptDialog
    global selectedSlave
    global slaveGroups
    global slaveDescription
    global slaveComment    
    for i in range(scriptDialog.GetValue( "InstancesBox" )):
        #===============================================
        # Preconfigure new slave instance
        #===============================================
        slaveInstanceName = str(selectedSlave[0] + '-' + string.ascii_uppercase[i])
        slaveInatance = RepositoryUtils.GetSlaveSettings(slaveInstanceName, True)
        slaveInatance.SlaveDescription = slaveDescription
        slaveInatance.SlaveComment = slaveComment
        try:
            RepositoryUtils.SaveSlaveSettings(slaveInatance)
            print("Slave instance'{0}' updated with properties from '{1}'.".format(slaveInstanceName, selectedSlave[0]))
        except Exception as e:
            print("Slave '{0}' failed to update. {1}.".format(slaveInstanceName, e.message.capitalize()))
        
        #===============================================
        # Launch new slave instance
        #===============================================   
        SlaveUtils.SendRemoteCommand( str(selectedSlave[0]), "LaunchNewSlave %s" %(string.ascii_uppercase[i]))
        print ( str(selectedSlave[0]), "LaunchNewSlave %s" %(string.ascii_uppercase[i]))
        RepositoryUtils.SetGroupsForSlave(str(selectedSlave[0] + '-' + string.ascii_uppercase[i]), slaveGroups)
        
        
        
        
        

        
        
        
    