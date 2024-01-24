from Deadline.Events import *
from Deadline.Scripting import *
from Deadline.Jobs import *
from System.IO import *

metaScriptDialog = None

def GetDeadlineEventListener():
    return HouseCleaningEvent()


def CleanupDeadlineEventListener(eventListener):
    eventListener.Cleanup()


class HouseCleaningEvent (DeadlineEventListener):
    def __init__(self):
        self.OnHouseCleaningCallback += self.OnHouseCleaning
    
    def Cleanup(self):
        del self.OnHouseCleaningCallback

    # Utility function that creates a Deadline Job based on given parameters
    def OnHouseCleaning(self):
        print("Howdy!")
        self.updatePools()
        
        
    def updatePools(self):
        global metaScriptDialog    
        priorityDoc = "\custom\Pool_Priorities.txt"
        root = "\\\\renderfarm8\DeadlineRepository8"
        docPath = root + priorityDoc    
        text_file = open(docPath, "r")
        priorityList = text_file.readlines()
        priorityList = [s.rstrip() for s in priorityList]
        existingPools = RepositoryUtils.GetPoolNames()
        slaveNames = RepositoryUtils.GetSlaveNames(True)
        
        ## Delete old pools from Repository
        for pool in existingPools:        
            if str(pool) != 'none':
                # print ("Deleting:", str(pool))
                RepositoryUtils.DeletePool(str(pool))
        
        ## Add Pools to Repository
        for pool in priorityList:
            try:
                # print ("Adding:", pool)
                RepositoryUtils.AddPool(pool)
            except:
                print ("Pool %s already exists" % (pool))        
            
        ## Set the slaves pool list
        for slave in slaveNames:
            RepositoryUtils.SetPoolsForSlave( slave, priorityList )
        

    
