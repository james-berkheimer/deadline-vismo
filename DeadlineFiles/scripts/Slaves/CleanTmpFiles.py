from System.IO import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


def __main__():
    print ("----")
    selectedSlaveInfoSettings = MonitorUtils.GetSelectedSlaveInfoSettings()
    machineNames = SlaveUtils.GetMachineNameOrIPAddresses(selectedSlaveInfoSettings)
    for machineName in machineNames:
        print machineName
        # SlaveUtils.SendRemoteCommand( machineName, "Execute cmd /C schtasks /Run /TN 'Temp Clean Up'" )
        results = SlaveUtils.SendRemoteCommandWithResults( machineName, "Execute cmd /C schtasks /Run /TN \"Temp Clean Up\"" )