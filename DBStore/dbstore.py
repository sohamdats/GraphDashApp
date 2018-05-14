'''
    Storing the container stat information in mongodb database
'''

from datetime import datetime,timedelta
from pymongo import MongoClient
from pymongo.operations import DeleteOne,InsertOne
import docker
import json
from time import sleep
import os
import logging

#-----------Logging-----------------------------------------------

'''
   This snippet will be separated out in a different file later
'''

dir_path = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__file__)
hdlr = logging.FileHandler(os.path.join(dir_path,'{}.log'.format(__file__.split('.')[0])))
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

#-------------------------------------------------------------------------




class dockerGuest:
    '''
       This class is used for collecting the list of docker containers in the target host 
       and retrieving their cpu,memory usage correspondnig to a particular timestamp

    '''
    def __init__(self,config_file):
        '''
            Initialisation: connecting to a particular host
            config_file contains the target host IP provided in obj initialisation 
        '''
        self.config_file=config_file
        self.client = docker.APIClient(base_url = self.get_url(self.config_file))


    def get_url(self,config_file):

        '''
            Getting the target host ip from config_file
        '''
        
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path,config_file)
        config_data = json.load(open(file_path))
        host = config_data["host"]
        port = config_data["port"]
        if host=="localhost" or host=="127.0.0.1":
            return "unix://var/run/docker.sock" #local
        else:
            return "tcp://{}:{}".format(host,port) #remote
        
        
    def container_list(self):
        '''
          Returning list of containers
        ''' 
        return self.client.containers()

    def get_stats(self):
        '''
            Returning container stat list
        '''
        stat_list = []
        container_list = self.container_list()
        if len(container_list) == 0:
            return None
        
        for container in container_list:
            '''
                For each containers extract the cpu memory usage and push it in 
                global list  stat_list  
            '''
            _id = container['Id']
            _dict = self.client.stats(container=_id,stream=False)
            stat_dict = {}
            stat_dict["_id"] = _id
            stat_dict["name"] = _dict["name"][1:]
            stat_dict["cpu_usage"] = _dict["cpu_stats"]["cpu_usage"]["total_usage"]     #cpu usage at this instant 
            stat_dict["system_cpu_usage"] = _dict["cpu_stats"]["system_cpu_usage"]      #system usage
            stat_dict["pre_cpu_usage"] = _dict["precpu_stats"]["cpu_usage"]["total_usage"] #last CPU usage         
            stat_dict["presystem_usage"]=_dict["precpu_stats"]["system_cpu_usage"]     #last system usage
            online_cpus = _dict["cpu_stats"]["online_cpus"]     #no of cpus used in system
            if online_cpus == 0.0:
                online_cpus = len(_dict["cpu_stats"]["cpu_usage"]["percpu_usage"])
            stat_dict["online_cpus"] = online_cpus
            stat_dict["memory_usage"] = _dict["memory_stats"]["usage"]
            stat_list.append(stat_dict)
            
        return stat_list    # return global list 

class Stat:
    '''
       This class is used  for
        1. Putting stat_list corresponsing to a specific timestamp
        2. Saving in mongoDB
    '''
    
    def __init__(self,config_file):
        self.docker = dockerGuest(config_file)
        self.config_file = config_file
        self.collection = MongoClient()['test'][self.get_collection()] # connecting to mongodb
        

    def get_collection(self):
        '''
          Getting mongodb collection(table) name from config file 
         (This method might be removed later...

       '''
        dir_path = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(dir_path,self.config_file)
        return json.load(open(file_path))["collection"]

    
    def get_config_file(self):
        return self.config_file
        
    @staticmethod
    def get_time():
        '''Getting current timestamp
      
           Storing python datetime object in mongodb.
           This might be changed later.
        '''        
        time = datetime.now()
        return time
    
    def data_to_save(self):
        '''
           Formats data to be saved in mongodb.
           JSON:
                {
                   time: timestamp,
                   stats: [{container1 stat },{ container2 stat } ...]
                }
        '''
        stats = self.docker.get_stats()
        if stats == None:  # if no stat that is there are no containers return None
            return None
        global_stat_dict ={}
        global_stat_dict["time"]=Stat.get_time()
        global_stat_dict["stats"] = stats
        return global_stat_dict

    def save(self,cap=60):
        ''' Saving in DB'''
        
        new_doc = self.data_to_save()
        if self.collection.count() == cap:
            '''
                If there are 60 items in db we delete the oldest timestamp data from db
                and insert the new item. We cannot simply delete an item because insertion in mongodb collection 
                is found out to be random.

            '''
            top_doc_time = min(doc['time'] for doc in self.collection.find()) #oldest timestamp. Simple if datetime objects are stored.
            self.collection.delete_one({'time':top_doc_time})  #delete oldest timestamp
            logger.info("Deleted timestamp is...{}".format(top_doc_time))   
        self.collection.insert_one(new_doc)  #insert new data
        logger.info("Saved in DB...{}".format(new_doc["time"]))


    def save_data(self):
       ''' method not used '''
       
        data = self.data_to_save()
        if data!=None:
            if self.is_db_full():
                self.make_space_db()
            self.collection.insert_one(data)
            logger.info('Saved in DB...')
            
    def save_to_db(self):
        ''' method not used'''
        
        data = self.data_to_save()
        
        if data != None:
            logger.info('DB Save')
            self.collection.insert_one(data)

    def make_space_db(self):
        '''not used'''
        logger.info('Making space')
        self.collection.delete_one({'_id':self.collection.find()[0]['_id']})
        

    def is_db_full(self,cap=60):
        '''not used'''
        
        if self.collection.find().count() == cap:
            return True
        return False

def get_scheduled_job():

    ''' config.json contains target host ip and collection name'''

    stat = Stat('config.json')
    logger.info('Main Job')
    stat.save()
            
get_scheduled_job()
