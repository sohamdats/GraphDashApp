'''
   This file is used to get the list of docker containers in the target host
   in Font-end
'''
import docker

class dockerGuest:
    def __init__(self):

        #self.client = docker.APIClient(base_url='tcp://64.103.196.51:2376')
        self.client = ''
        self.ip = '64.103.196.51:2376'

    def get_client(self,ip):
        ''' connecting to docker client in target host'''
        
        url = 'tcp://{}'.format(ip)
        return docker.APIClient(base_url=url)
    
    def image_list(self):
        self.client = self.get_client(self.ip)
        return [con['Image'] for con in self.client.containers()]

    
    def get_cont_list(self):

        ''' Getting info from the container list to be displayed in html table'''
        
        self.client = self.get_client(self.ip)
        cont_list = []
        for con in self.client.containers():
            cont_dict = {}
            cont_dict['Id'] = con['Id']
            cont_dict['Image'] = con['Image']
            cont_dict['name'] = con['Names'][0][1:]
            #cont_dict['IPAddress'] = con['NetworkSettings']['Networks']['bridge']['IPAddress']
            #cont_dict['Gateway'] = con['NetworkSettings']['Networks']['bridge']['Gateway']
            for val in con['NetworkSettings']['Networks'].values():
                cont_dict['IPAddress'] = val['IPAddress']
                cont_dict['Gateway'] = val['Gateway']
            cont_list.append(cont_dict)  

        return cont_list  #returning list to be displayed in table
    
    def get_ip(self,name):
        ''' getting ip address of a particular container given the name'''
        
        self.client = self.get_client(self.ip)
        for con in self.client.containers():
            for con_name in con['Names']:
                if con_name[1:] == name:
                    for val in con['NetworkSettings']['Networks'].values():
                        return val['IPAddress']
    
    
            
