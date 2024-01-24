from System.IO import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from DeadlineUI.Controls.Scripting.DeadlineScriptDialog import DeadlineScriptDialog


# def __main__():    
#     print ("----")
#     print ("RepositoryUtils.GetSlaveInfoSettings(selectedSlave[0], True)")
#     selectedSlave = MonitorUtils.GetSelectedSlaveNames()
#     for i in RepositoryUtils.GetSlaveInfoSettings(selectedSlave[0], True):
#         print i.Settings
#         
#     print ("----")
#     print ("MonitorUtils.GetSelectedSlaveSettings()")
#     for i in MonitorUtils.GetSelectedSlaveSettings():
#         print i
#     
#     print ("----")
#     print ("MonitorUtils.GetSelectedSlaveInfoSettings()")
#     for i in MonitorUtils.GetSelectedSlaveInfoSettings():
#         print i

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
      
      # slave_settings.SlaveComment = "Testing"
      # print ("---")
      # print 'SlaveComment Changed :',slave_settings.SlaveComment 