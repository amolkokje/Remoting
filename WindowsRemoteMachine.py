import os, sys, subprocess, re, time
import win32api, logging
from string import ascii_uppercase
from RemoteMachine import RemoteMachine


class WindowsRemoteMachine(RemoteMachine):  

    def __init__(self, machine_ip, machine_name, machine_username, machine_password, psexec_exe, enable_remoting=True, log_level='INFO'):
                
        # use 'super' to call a method defined in the parent class. The call below calls the constructor from parent class.
        super(WindowsRemoteMachine, self).__init__(machine_ip, machine_name, machine_username, machine_password)
        
        self.machine_type='windows'
        self.psexec_exe=psexec_exe

        # setup logging - change level to DEBUG to view all the activity
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt="%Y%m%d-%H%M%S")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.debug("Machine {0} of type {1} init done".format(self.machine_name, self.machine_type))

        if enable_remoting:
            self.enable_remoting()

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

    def enable_remoting(self):
        self.logger.debug("Enable WinRM on machine {0}".format(self.machine_ip))
        self._execute_psexec_command("powershell Enable-PSRemoting -Force")

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
        file_path = file_path.replace(':','$')
        file_path = "\\\\{0}\\{1}".format(self.machine_ip, file_path)
        return os.path.exists(file_path) and os.path.isfile(file_path)

    def check_folder_exists(self, folder_path):
        folder_path = folder_path.replace(':','$')
        folder_path = "\\\\{0}\\{1}".format(self.machine_ip, folder_path)
        return os.path.exists(folder_path) and os.path.isdir(folder_path)

    # --------------------------------------------------
    # SET METHODS
    # --------------------------------------------------

    def set_reg_key_value(self, path, key, value):
        self._execute_powershell_command("Set-ItemProperty -Path {0} -Name {1} -Value {2}".format(path, key, value))

    # --------------------------------------------------
    # GET METHODS
    # --------------------------------------------------

    def get_reg_key_value(self, path, key):
        output_rows = self._execute_powershell_command("Get-ItemProperty -Path {0} -Name {1}".format(path, key))
        regex_string = r"({0})(\s*:\s*)(.*)".format(key)
        match_obj = re.match(regex_string, output_rows[0])
        if match_obj and match_obj.group(3):
            return match_obj.group(3)
        return None

    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    def download_file(self, local_destination, remote_destination, file_name):
        self.logger.debug("Downloading file {} FROM={}, TO={}".format(file_name, remote_destination, local_destination))
        
        remote_destination_drive, remote_destination_subdir = os.path.splitdrive(remote_destination)
        remote_destination_drive = remote_destination_drive.replace(':','$')
        remote_destination_drive = os.path.join("\\\\{0}".format(self.machine_ip), remote_destination_drive)

        map_drive = WindowsRemoteMachine.get_unused_drive()
        self._run_system_command("net use {0} {1} /u:{2} {3}".format(map_drive, remote_destination_drive,
                                                                     self.machine_username, self.machine_password))
        remote_file_path = os.path.join(map_drive, '\\', remote_destination_subdir)
        # check if remote file exists
        if not os.path.exists(remote_file_path):
            self.logger.error("file {} does not exist.".format(remote_file_path))
            return False
        # creates directory path if does not exist
        self._execute_robocopy_command(remote_file_path, local_destination, file_name)
        self._run_system_command("net use {0} /d".format(map_drive))
        local_file_path=os.path.join(local_destination, file_name)
        return os.path.exists(local_file_path) and os.path.isfile(local_file_path)

    def download_folder(self, local_destination, remote_destination):
        self.logger.debug("Downloading folder FROM={}, TO={}".format(remote_destination, local_destination))
        
        remote_destination_drive, remote_destination_subdir = WindowsRemoteMachine.get_remote_destination_drive_path\
            (self.machine_ip, remote_destination)

        map_drive = WindowsRemoteMachine.get_unused_drive()
        self._run_system_command("net use {0} {1} /u:{2} {3}".format(map_drive, remote_destination_drive,
                                                                     self.machine_username, self.machine_password))
        # creates directory path if does not exist
        self._execute_robocopy_command(os.path.join(map_drive, '\\', remote_destination_subdir), local_destination)
        self._run_system_command("net use {0} /d".format(map_drive))
        return os.path.exists(local_destination) and os.path.isdir(local_destination)

    # --------------------------------------------------
    # UPLOAD
    # --------------------------------------------------
    
    def upload_file(self, local_destination, remote_destination, file_name):
        self.logger.debug("Uploading file {0} FROM={1}, TO={2}".format(file_name, local_destination, remote_destination))
        
        remote_destination_drive, remote_destination_subdir = WindowsRemoteMachine.get_remote_destination_drive_path\
            (self.machine_ip, remote_destination)
        
        map_drive = WindowsRemoteMachine.get_unused_drive()
        self._run_system_command("net use {0} {1} /u:{2} {3}".format(map_drive, remote_destination_drive, self.machine_username, self.machine_password))
        # creates directory path if does not exist    
        self._execute_robocopy_command(local_destination, os.path.join(map_drive, '\\', remote_destination_subdir), file_name)
        self._run_system_command("net use {0} /d".format(map_drive))
        return self.check_file_exists(os.path.join(remote_destination,file_name))
    
    
    def upload_folder(self, local_destination, remote_destination):
        self.logger.debug("Uploading folder FROM={0}, TO={1}".format(local_destination, remote_destination))
        
        remote_destination_drive, remote_destination_subdir = WindowsRemoteMachine.get_remote_destination_drive_path \
            (self.machine_ip, remote_destination)

        map_drive = WindowsRemoteMachine.get_unused_drive()
        self._run_system_command("net use {0} {1} /u:{2} {3}".format(map_drive, remote_destination_drive, self.machine_username, self.machine_password))                
        # creates directory path if does not exist
        self._execute_robocopy_command(local_destination, os.path.join(map_drive, '\\', remote_destination_subdir))
        self._run_system_command("net use {0} /d".format(map_drive))
        return self.check_folder_exists(remote_destination)

    # --------------------------------------------------
    # SERVICE
    # --------------------------------------------------

    def service_status(self, service_name):
        output_rows=self._execute_powershell_command("Get-Process {}".format(service_name))
        if ((not output_rows) or (service_name not in output_rows[-1])):
            return False
        return True

    def service_start(self, service_name, timeout=5):        
        """ unable to do this reliably directly through powershell Start-Process or using task using name directly.
        Only possible way is to use PsExec.exe with full process path """
        pass

    def service_stop(self, service_name, timeout=5):
        if self.service_status(service_name):
            if '.exe' not in service_name:
                service_name=service_name+'.exe'
            self.logger.debug("Stopping service {}".format(service_name))
            self.execute_command("taskkill /im {} /f".format(service_name))
        else:
            return True           
        
        end_time=time.time()+timeout
        while end_time > time.time():
            if self.service_status(service_name):
                self.logger.debug("Waiting for service {} to stop".format(service_name))
                time.sleep(1)
            else:
                self.logger.debug("Service {} stopped successfully".format(service_name))
                return True
        if self.service_status(service_name):
            self.logger.debug("Unable to stop {} after timeout {} seconds expired".format(service_name, timeout))
            return False
        else:
            self.logger.debug("Service {} started successfully".format(service_name))
            return True

    # --------------------------------------------------
    # EXECUTE
    # --------------------------------------------------

    def execute_command(self, command):
        return self._execute_psexec_command(command)

    # --------------------------------------------------
    # UTILS
    # --------------------------------------------------
    
    def _execute_powershell_command(self, command):
        file_name = 'remote_powershell_script.ps1'
        content = "$sec_password=ConvertTo-SecureString \"{0}\" -AsPlainText -Force \n" \
                  "$my_creds=New-Object System.Management.Automation.PSCredential(\"{1}\",$sec_password) \n" \
                  "Invoke-Command -ComputerName {2} -Command {{{3}}} -Credential $my_creds " \
                  "\n".format(self.machine_password, self.machine_username, self.machine_name, command)
        with open(file_name,'w') as fh:
            fh.write(content)
        output = self._run_system_command("powershell -ExecutionPolicy Bypass -File {0}".format(file_name)).split("\n")
        os.remove(file_name)
        return output

    def _execute_robocopy_command(self, source, destination, file_name=None):
        """
        robocopy error codes:
        0x10 Serious error. Robocopy did not copy any files. This is either a usage error or an error due to
        insufficient access privileges on the source or destination directories.
        0x08 Some files or directories could not be copied (copy errors occurred and the retry limit was exceeded).
        Check these errors further.
        0x04 Some Mismatched files or directories were detected. Examine the output log.
        Housekeeping is probably necessary.
        0x02 Some Extra files or directories were detected. Examine the output log. Some housekeeping may be needed.
        0x01 One or more files were copied successfully (that is, new files have arrived).
        0x00 No errors occurred, and no copying was done. The source and destination directory trees are completely
        synchronized.
        """
        try:
            if (file_name is None):
                cmd = "robocopy \"{0}\" \"{1}\" /E".format(source, destination)
            else:
                cmd = "robocopy \"{0}\" \"{1}\" {2}".format(source, destination, file_name)
            self._run_system_command(cmd)
        except subprocess.CalledProcessError as ex:
            if int(ex.returncode) == 1:
                self.logger.debug("One or more files were copied successfully")
            else:
                raise 

    def _execute_psexec_command(self, command):
        psexec_command = "{0} \\\\{1} -n 15 -u \"{2}\" -p \"{3}\" -h {4}".format(self.psexec_exe, self.machine_ip,
                                                                                 self.machine_username,
                                                                                 self.machine_password, command)
        self._run_system_command(psexec_command)

    def _run_system_command(self, cmd, sleep=None):
        try:
            self.logger.debug("CMD='{0}'".format(cmd))
            output = subprocess.check_output(cmd, shell=True).strip()
            if output:
                self.logger.debug("CMD Output='{0}'".format(output))
            if sleep:
                time.sleep(sleep)
            return str(output)
        except subprocess.CalledProcessError as ex:
            raise       # raise all subprocess errors so that they can be handled appropriately by calling code           

    """static methods are standalone. Neither 'self' or class instance is passed implicitly as the first argument.
    They behave like plain functions. You can call below mehod directly from any python code without a class instance:
    from WindowsRemoteMachine import WindowsRemoteMachine
    print WindowsRemoteMachine.get_unused_drive()
    """
    @staticmethod
    def get_unused_drive():
        """
        waits and gives an unmounted drive letter.
        :return: string letter
        """
        # wait loop if drive not found, so can run in parallel and queue up
        drives = win32api.GetLogicalDriveStrings()        
        drives = drives.split(':\\\x00')[:-1]

        while(True):            
            unused_drives = list()
            for c in ascii_uppercase:
                if c not in drives:
                    if not ((c is 'A') or (c is 'B') or (c is 'C') or (c is 'D')):
                        unused_drives.append(c)
            if unused_drives:
                return unused_drives[0]+":"

    @staticmethod
    def get_remote_destination_drive_path(ip, path):
        """
        constructs remote path based on remote machine ip and path
        :param ip: sample: 10.84.222.45
        :param path: C:\\temp\\test
        :return: \\10.84.222.45\C$, \temp\test
        """
        drive, subdir = os.path.splitdrive(path)
        drive = drive.replace(':','$')
        return os.path.join("\\\\{0}".format(ip), drive), subdir


