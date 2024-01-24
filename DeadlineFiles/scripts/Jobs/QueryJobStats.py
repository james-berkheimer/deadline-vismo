"""
QueryJobStats.py - Example of how to calculate job statistics for a selected job and print to console the result for average frame render time & peak ram usage
Copyright Thinkbox Software 2016
"""

from System import TimeSpan
import os
import time
import datetime

from Deadline.Scripting import *
from Deadline.Jobs import *



def __main__():

    jobIds = MonitorUtils.GetSelectedJobIds()

    outputpath = 'C:\Users\jberkheimer\Desktop\Holding_Tank'
    filename = "BladeStats.txt"
    outputfile = open(os.path.join(outputpath, filename), "w")

    for jobId in jobIds:
        slaves = RepositoryUtils.GetSlavesRenderingJob(jobId)
        job = RepositoryUtils.GetJob(jobId, True)
        tasks = RepositoryUtils.GetJobTasks(job, True)
        
        jobStatsDict = {}
        for task in tasks:
            jobStatsDict.setdefault(task.SlaveName,[])            
        for task in tasks:
            jobStatsDict[task.SlaveName].append(task.TaskTime)
            
        for key, values in sorted(jobStatsDict.iteritems()):
            print "%s (%s Tasks):" % (key, len(values))
            outputfile.write( "%s (%s Tasks):" % (key, len(values)))
            outputfile.write("\n")
            for value in sorted(values):
                print "         %s" % (value)
                outputfile.write("         %s" % (value))
                outputfile.write("\n")
    outputfile.close()
                
    
            
        # filteredTaskTimes = []
        # for t in tasks:
        #     if "Render53" in t.SlaveName:
        #         print t.SlaveName
        #         print t.TaskTime
        #         filteredTaskTimes.append(t.TaskTime)
        # 
        # filteredTaskTimes = taskTimes
        # 
        # stats = JobUtils.CalculateJobStatistics(job, tasks)
        # stats = JobUtils.CalculateJobStatistics(job, filteredTaskTimes)
        # 
        # print sum(filteredTaskTimes)/len(filteredTaskTimes)
        # 
        # 
        # jobAverageFrameRenderTime = stats.AverageFrameRenderTime
        # jobPeakRamUsage = stats.PeakRamUsage / 1024 / 1024
        # 
        # timeSpan = jobAverageFrameRenderTime
        # print jobAverageFrameRenderTime
        # timeSpan = "%02dd:%02dh:%02dm:%02ds" % (timeSpan.Days, timeSpan.Hours, timeSpan.Minutes, timeSpan.Seconds)
        #         
        # print("JobAverageFrameRenderTime: %s" % timeSpan)
        # print("JobPeakRamUsage: %sMb" % jobPeakRamUsage)