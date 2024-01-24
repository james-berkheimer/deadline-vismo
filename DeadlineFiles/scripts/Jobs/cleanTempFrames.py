import os, glob
import subprocess

from Deadline.Scripting import *
from Deadline.Jobs import *




def __main__():
    print ("----")   
    selectedJobs = MonitorUtils.GetSelectedJobs()
    for job in selectedJobs:
        # print ('got:', job)
        pluginInfoKeys = job.GetJobPluginInfoKeys()
        jobInfoKeys = job.GetJobInfoKeys()
        #OutputDirectory0
        for key in jobInfoKeys:
            # print (key)
            if key == "OutputDirectory0":
                outputDirectory = job.GetJobInfoKeyValue(key)
                print(outputDirectory)   
            if key == "OutputFilename0":
                filename = job.GetJobInfoKeyValue(key)
                
        for file in sorted(os.listdir(outputDirectory)):
            ext = filename.split("_####")[1]
            if file.endswith(ext):
                print("Publishing: %s " % (file))
                # os.remove(os.path.join(outputDirectory, file))