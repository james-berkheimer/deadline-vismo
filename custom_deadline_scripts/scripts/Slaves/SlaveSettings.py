from System.IO import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


def __main__():
    print ("----")
    selectedSlaves = MonitorUtils.GetSelectedSlaveNames()    
    for slave_name in selectedSlaves:        
        print 'got:', slave_name
        slave_settings = RepositoryUtils.GetSlaveSettings(slave_name, True)
        #
        print 'SlaveDescription:',slave_settings.SlaveDescription
        print 'SlaveComment :',slave_settings.SlaveComment
        print 'SlaveGroups :', [str(thing) for thing in slave_settings.SlaveGroups]
        print 'SlavePools :', [str(thing) for thing in slave_settings.SlavePools]