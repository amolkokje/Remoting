import os, sys, re, time
import paramiko
import logging
from RemoteMachine import RemoteMachine


class LinuxRemoteMachine(RemoteMachine):

    def __init__(self, machine_ip, machine_name, machine_username, machine_password, log_level='INFO'):
        # use 'super' to call a method defined in the parent class.
        # The call below calls the constructor from parent class.
        super(LinuxRemoteMachine, self).__init__(machine_ip, machine_name, machine_username, machine_password)
        
        self.machine_type='linux'
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh_port = 22
        self.ssh.connect(self.machine_ip, username = self.machine_username, password = self.machine_password,
                         port = self.ssh_port)
        self.ftp = self.ssh.open_sftp()

        # setup logging - change level to DEBUG to view all the activity
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt="%Y%m%d-%H%M%S")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.debug("Machine {0} of type {1} init done".format(self.machine_name, self.machine_type))

        if log_level:
            self.set_log_level(log_level)
        else:
            self.set_log_level('INFO')

    # --------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------
    # https://www.programiz.com/python-programming/property
    
    @property
    def ip(self):
        return self.machine_ip
        
    @property
    def name(self):
        return self.machine_name
        
    @property
    def type(self):
        return self.machine_type

    # --------------------------------------------------
    # SETUP
    # --------------------------------------------------

    def set_log_level(self, level):
        if level == 'DEBUG':
            self.logger.setLevel(logging.DEBUG)
        elif level == 'INFO':
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.INFO)

    # --------------------------------------------------
    # CHECK METHODS
    # --------------------------------------------------

    def check_file_exists(self, file_path):        
        return self.check_folder_exists(file_path)

    def check_folder_exists(self, folder_path):
        try:
            self.ftp.stat(folder_path)  
            return True
        except IOError:
            return False

    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    def download_file(self, local_destination, remote_destination, file_name):
        self.logger.debug("Downloading file {} FROM={}, TO={}".format(file_name, remote_destination, local_destination))
        # check if local folder exists
        if not os.path.exists(local_destination):
            os.makedirs(local_destination)
        # check if remote file exists
        remote_file_path = os.path.join(remote_destination, file_name)
        local_file_path = os.path.join(local_destination, file_name)
        if self.check_file_exists(remote_file_path):
            self.ftp.get(remote_file_path, local_file_path)
            return os.path.exists(os.path.join(local_destination, file_name))        
        else:
            return False        

    def download_folder(self, local_destination, remote_destination):
        self.logger.debug("Downloading folder FROM={}, TO={}".format(remote_destination, local_destination))
        # check if local folder exists
        if not os.path.exists(local_destination):
            os.makedirs(local_destination)
        # check if remote folder exists
        if not self.check_folder_exists(remote_destination):
            return False
        # download each file one by one from remote location
        self.ftp.chdir(remote_destination)
        for file in self.ftp.listdir():
            if not self.download_file(local_destination, remote_destination, file):
                self.logger.error("Problem while downloading file {}!".format(os.path.join(remote_destination, file)))
                return False
        return True

    # --------------------------------------------------
    # UPLOAD
    # --------------------------------------------------

    def upload_file(self, local_destination, remote_destination, file_name):
        self.logger.debug("Uploading file {0} FROM={1}, TO={2}".format(file_name, local_destination, remote_destination))
        local_file_path=os.path.join(local_destination, file_name)
        remote_file_path=os.path.join(remote_destination, file_name)
        # check local file exists
        if not os.path.exists(local_file_path):
            self.logger.error("No file exists in local machine at path {}!".format(local_file_path))
            return False
        # check remote path exists
        if not self.check_folder_exists(remote_destination):
            self.logger.debug("No folder exists in remote machine at path {}!".format(remote_destination))
            self._mkdir_path(remote_destination)
        # upload file
        self.ftp.put(local_file_path, remote_file_path)
        return self.check_file_exists(os.path.join(remote_destination,file_name))

    def upload_folder(self, local_destination, remote_destination):
        self.logger.debug("Uploading folder FROM={0}, TO={1}".format(local_destination, remote_destination))
        # check local folder exists
        if not os.path.exists(local_destination):
            self.logger.error("No file exists in local machine at path {}!".format(local_destination))
            return False
        # check remote dir exists
        if not self.check_folder_exists(remote_destination):
            self.logger.debug("No folder exists in remote machine {}. Creating directory tree".format(remote_destination))
            self._mkdir_path(remote_destination) 
            
        file_list=os.listdir(local_destination)
        for file in file_list:
            if not self.upload_file(local_destination, remote_destination, file):
                self.logger.error("Problem while uploading file {}!".format(os.path.join(local_destination, file)))
                return False
        return True

    # --------------------------------------------------
    # SERVICE
    # --------------------------------------------------

    def service_status(self, service_name):
        output=self.execute_command('service {} status'.format(service_name))
        if not output:
            self.logger.debug("No service found with name '{}'!".format(service_name))
            return None
        if 'stopped' in output:
            self.logger.debug("Service '{}' is not running".format(service_name))
            return False
        if 'running' in output:
            self.logger.debug("Service '{}' is running".format(service_name))
            return True

    def service_start(self, service_name, timeout=5):
        if not self.service_status(service_name):
            self.logger.debug("Starting service {}".format(service_name))
            self.execute_command('service {} start'.format(service_name))
        else:
            return True
        # wait for time out
        end_time = time.time()+timeout
        while end_time > time.time():
            if not self.service_status(service_name):
                self.logger.debug("Waiting for service {} to start".format(service_name))
                time.sleep(1)
            else:
                return True
        # final check
        if not self.service_status(service_name): 
            self.logger.debug("Unable to start {} after timeout {} seconds expired".format(service_name, timeout))
            return False
        else:
            return True

    def service_stop(self, service_name, timeout=5):
        if self.service_status(service_name):
            self.logger.debug("Stopping service {}".format(service_name))
            self.execute_command('service {} stop'.format(service_name))
        else:
            return True
        # wait for time out
        end_time = time.time()+timeout
        while end_time > time.time():
            if self.service_status(service_name):
                self.logger.debug("Waiting for service {} to stop".format(service_name))
                time.sleep(1)
            else:
                return True
        # final check
        if self.service_status(service_name):
            self.logger.debug("Unable to stop {} after timeout {} seconds expired".format(service_name, timeout))
            return False
        else:
            return True

    # --------------------------------------------------
    # EXECUTE
    # --------------------------------------------------

    def execute_command(self, command):
        return self._run_system_command(command)

    # --------------------------------------------------
    # UTILS
    # --------------------------------------------------

    def _run_system_command(self, cmd):
        self.logger.debug("CMD='{}'".format(cmd))
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        cmd_output=stdout.read()
        self.logger.debug("CMD Output='{}'".format(cmd_output))
        return cmd_output

    def _mkdir_path(self, remote_directory):
        """ makes the directory tree recursively, if it does not exist """
        self.logger.debug("remote directory = {}".format(remote_directory))
        if remote_directory == '/':
            # absolute path so change directory to root
            self.ftp.chdir('/')
            return
        if remote_directory == '':
            # top-level relative directory must exist
            return
        try:
            self.ftp.chdir(remote_directory) # sub-directory exists
        except IOError:
            # exception when sub-directory does not exist
            dirname, basename = os.path.split(remote_directory.rstrip('/'))
            self.logger.debug("d={} b={}".format(dirname, basename))
            self._mkdir_path(dirname) # make parent directories
            self.ftp.mkdir(basename) # sub-directory missing, so created it
            self.ftp.chdir(basename)
            return True

    # --------------------------------------------------
    # CUSTOM EXCEPTIONS
    # --------------------------------------------------
