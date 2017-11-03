import abc
from abc import abstractmethod
from exceptions import NotImplementedError

class RemoteMachine(object):
    __metaclass__=abc.ABCMeta
    
    def __init__(self, machine_ip, machine_name, machine_username, machine_password):
        print "RemoteMachine __init__()"
        self.machine_ip=machine_ip
        self.machine_name=machine_name
        self.machine_username=machine_username
        self.machine_password=machine_password
    
    ## a method with @abstractmethod decorator has to be implemented in the child class     
        
    @abstractmethod
    def check_file_exists(self, file_path):
        raise NotImplementedError()
        
        
    @abstractmethod    
    def check_folder_exists(self, folder_path):
        raise NotImplementedError()
        
        
    @abstractmethod
    def download_file(self, local_destination, remote_destination, file_name):    
        raise NotImplementedError()
   
   
    @abstractmethod
    def download_folder(self, local_destination, remote_destination):
        raise NotImplementedError()
        
    
    @abstractmethod
    def upload_file(self, local_destination, remote_destination, file_name):
        raise NotImplementedError()
        
        
    @abstractmethod
    def upload_folder(self, local_destination, remote_destination):
        raise NotImplementedError()
        
        
    @abstractmethod
    def service_status(self, service_name):
        raise NotImplementedError()
        
    
    @abstractmethod
    def service_start(self, service_name, timeout=5):
        raise NotImplementedError()
        
        
    @abstractmethod
    def service_stop(self, service_name, timeout=5):
        raise NotImplementedError()    
