'''
   Retrieving information from mongoDB
'''
from pymongo import MongoClient
from datetime import datetime


class mongoGuest:
    def __init__(self):
        self.collection = MongoClient()['test']['timestamp'] # connecting to mongodb client in target host
        
    def find_cpu_percentage(self,con):
        ''' Argument con containers the stat info of a particular container.
            This method calculates the cpu usage percentage.

             CPU usage percentage calculation:
               
             (cpu usage now - cpu usage at last instant)/(system usage now - system usage at last instant)* total no of cpus * 100
            
          For further info go to:
          https://github.com/docker/cli/blob/1401d5daf2f49a97791487dd5c5a8598907f0bf1/cli/command/container/stats_helpers.go#L103-L105
          or
          https://github.com/docker/cli/blob/1401d5daf2f49a97791487dd5c5a8598907f0bf1/cli/command/container/stats_helpers.go#L168-L185

        '''
        cpu_usage = con["cpu_usage"]
        system_usage = con["system_cpu_usage"]
        precpu_usage= con["pre_cpu_usage"]
        presystem_usage = con["presystem_usage"]
        online_cpus = con["online_cpus"]
        cpu_delta = (cpu_usage - precpu_usage)
        system_delta = (system_usage - presystem_usage)
        
        if cpu_delta >0.0 and system_delta > 0.0:
            return (cpu_delta/system_delta) * online_cpus *100.0
        else:
            return 0.0


    def get_cpu_usage(self,cont_name,percent=False):
        ''' 
           Get cpu usage of a particular container given container name.
           Return cpu_usage in percentage if percent==True else return cpu_usage in ns.
           (  To understand the format of the data that is saved you have to go to DBStore/dbstore.py  )
        '''        
        time = 1  #X-axis values
        timestamps = []  #storing sorted timestamps 

        X = []   # X-asis of graph (timestamps)
        Y = []   # Y-axis (cpu_usage)
        
        for doc in self.collection.find():
            ''' Sort the timestamps because insertion in db is random.
                 This might be removed later
            '''
            timestamps.append(doc["time"])
        timestamps.sort()  
         
        for ts_obj in timestamps: # iterate over sorted timestamps
            doc = self.collection.find({'time':ts_obj})[0]
            for con in doc['stats']:
                ''' find the particular container'''
                
                if con['name'] == cont_name:
                    if percent==True:
                        Y.append(self.find_cpu_percentage(con))
                    else:
                        Y.append(con["cpu_usage"])
                    X.append(time)
                    time+=1

        return (X,Y)  

    def get_memory_usage(self,cont_name):

        ''' same as CPU usage above'''
        
        time = 1
        timestamps = []
        X = []
        Y = []
        for doc in self.collection.find():
            timestamps.append(doc["time"])
        timestamps.sort()
        for ts_obj in timestamps:
            doc = self.collection.find({'time':ts_obj})[0]
            for con in doc['stats']:
                if con['name'] == cont_name:
                    Y.append(con['memory_usage'])
                    X.append(time)
                    time+=1
        return (X,Y)
       
