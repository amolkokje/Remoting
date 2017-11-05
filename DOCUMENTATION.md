
    # --------------------------------------------------
    # PROPERTIES
    # --------------------------------------------------
    @property
    def ip(self):
        """
        machine ip
        :return:  ip address of remote machine
        """

    @property
    def name(self):
        """
        machine host name
        :return: hostname of remote machine
        """
        
    @property
    def type(self):
        """
        machine os type
        :return: os type of remote machine
        """

    # --------------------------------------------------
    # SETUP
    # --------------------------------------------------

    def enable_remoting(self):
        """
        enable WinRM for remoting on the remote machine
        :return: None
        """

    def set_log_level(self, level):
        """
        set the logging level of the class
        :param level: log level to set for the object
        :return: None
        """


    # --------------------------------------------------
    # CHECK METHODS
    # --------------------------------------------------
    
    def check_file_exists(self, file_path):
        """
        check if the file exists on remote machine
        :param file_path: path on the remote machine
        :return: True/False
        """

    def check_folder_exists(self, folder_path):
        """
        check if the folder exists on remote machine
        :param folder_path: path on the remote machine
        :return: True/False
        """

    # --------------------------------------------------
    # SET METHODS
    # --------------------------------------------------

    def set_reg_key_value(self, path, key, value):
        """
        set registry key on remote machine to value
        :param path: path of key in registry editor
        :param key: key name
        :param value: key value
        :return: output of powershell command executed
        """

    # --------------------------------------------------
    # GET METHODS
    # --------------------------------------------------

    def get_reg_key_value(self, path, key):
        """
        get the registry value using specific key
        :param path: path of key in registry editor
        :param key: key name
        :return: key value output of the powershell command
        """

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

    def download_folder(self, local_destination, remote_destination):
        """
        download folder from remote destination to local destination
        :param local_destination: path of folder on local machine
        :param remote_destination: path of folder on remote machine
        :return: true/false
        """

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

    def upload_folder(self, local_destination, remote_destination):
        """
        upload folder from local destination to remote folder destination
        :param local_destination: location on local machine
        :param remote_destination: location on remote machine
        :return: true/false
        """

    # --------------------------------------------------
    # SERVICE
    # --------------------------------------------------

    def service_status(self, service_name):
        """
        check if the service by name is running on remote machine
        :param service_name: name of service to check the status of
        :return: true/false
        """

    def service_start(self, service_name, timeout=5):
        """
        start service by name on remote machine
        :param service_name: name of service to start
        :param timeout: timeout for attempt to start
        :return: true/false
        """

    def service_stop(self, service_name, timeout=5):
        """
        stop the service by name on remote machine
        :param service_name: name of service to stop
        :param timeout: timeout for service to stop
        :return: true/false
        """

    # --------------------------------------------------
    # EXECUTE
    # --------------------------------------------------

    def execute_command(self, command):
        """
        execute command on remote machine
        :param command: command to execute on remote machine
        :return: output of command execution
        """

