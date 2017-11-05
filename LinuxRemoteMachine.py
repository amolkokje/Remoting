import os, sys, re, time
import paramiko
import logging
from RemoteMachine import RemoteMachine


class LinuxRemoteMachine(RemoteMachine):

    def __init__(self, machine_ip, machine_name, machine_username, machine_password, log_level='INFO'):
        """
        constructor
        :param machine_ip: ip address of remote machine
        :param machine_name: host name of remote machine
        :param machine_username: login username for remote machine
        :param machine_password: login password for remote machine
        :param psexec_exe: path to psexec exe
        :param log_level: set log level
        """
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
        """
        set the logging level of the class
        :param level: log level to set for the object
        :return: None
        """
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
        """
        check if the file exists on remote machine
        :param file_path: path on the remote machine
        :return: True/False
        """
        return self.check_folder_exists(file_path)

    def check_folder_exists(self, folder_path):
        """
        check if the folder exists on remote machine
        :param folder_path: path on the remote machine
        :return: True/False
        """
        try:
            self.ftp.stat(folder_path)  
            return True
        except IOError:
            return False

    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    def download_file(self, local_destination, remote_destination, file_name):
        """
        download file from remote destination path to destination on local machine
        :param local_destination: folder path on local machine
        :param remote_destination: folder path on remote machine
        :param file_name: file name to download
        :return: True/False
        """
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
        """
        download folder from remote destination to local destination
        :param local_destination: path of folder on local machine
        :param remote_destination: path of folder on remote machine
        :return: true/false
        """
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
        """
        upload file from local destination to remote machine destination
        :param local_destination: location on local machine
        :param remote_destination: location on remote machine
        :param file_name: name of file to upload
        :return: true/false
        """
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
        """
        upload folder from local destination to remote folder destination
        :param local_destination: location on local machine
        :param remote_destination: location on remote machine
        :return: true/false
        """
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
        """
        check if the service by name is running on remote machine
        :param service_name: name of service to check the status of
        :return: true/false
        """
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
        """
        start service by name on remote machine
        :param service_name: name of service to start
        :param timeout: timeout for attempt to start
        :return: true/false
        """
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
        """
        stop the service by name on remote machine
        :param service_name: name of service to stop
        :param timeout: timeout for service to stop
        :return: true/false
        """
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
        """
        execute command on remote machine
        :param command: command to execute on remote machine
        :return: output of command execution
        """
        return self._run_system_command(command)

    # --------------------------------------------------
    # UTILS
    # --------------------------------------------------

    def _run_system_command(self, cmd):
        """
        run system command on local machine synchronously
        :param cmd: command to execute on local machine
        :param sleep: time to sleep after executing the command
        :return: command output
        """
        self.logger.debug("CMD='{}'".format(cmd))
        stdin, stdout, stderr = self.ssh.exec_command(cmd)
        cmd_output=stdout.read()
        self.logger.debug("CMD Output='{}'".format(cmd_output))
        return cmd_output

    def _mkdir_path(self, remote_directory):
        """
        makes the directory tree recursively, if it does not exist
        :param remote_directory:
        :return: None
        """
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
