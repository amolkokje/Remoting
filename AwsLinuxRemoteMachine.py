import os, sys, re, time
import boto3
import logging
import botocore
#from RemoteMachine import RemoteMachine

## not exactly extending remote machine?
class AwsLinuxRemoteMachine():

    @staticmethod
    def create_aws_linux_machine(image_id, access_key_id, secret_access_key, region,
                                 instance_type='t2.micro'):
        """
        Creates an ami isntance in AWS, returns an AwsLinuxremoteMachine object
        :param instance_type:
        :param image_id:
        :param access_key_id:
        :param secret_access_key:
        :param region:
        :return:
        """
        ec2 = boto3.resource('ec2',
                             aws_access_key_id=access_key_id,
                             aws_secret_access_key=secret_access_key,
                             region_name=region)
        ec2_client = boto3.client('ec2',
                                  aws_access_key_id=access_key_id,
                                  aws_secret_access_key=secret_access_key,
                                  region_name=region)

        instances = ec2.create_instances(
            ImageId=image_id,
            MinCount=1,
            MaxCount=1,
            InstanceType=instance_type,
            IamInstanceProfile={'Name': 'SimpleSystemManagerRole'}
        )

        instance_id = str(instances[0].id)

        waiter = ec2_client.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[instance_id])

        return AwsLinuxRemoteMachine(instance_id, access_key_id, secret_access_key, region)

    def __init__(self, instance_id, access_key_id, secret_access_key, region, log_level='INFO'):
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
        #super(AwsLinuxRemoteMachine, self).__init__(machine_ip, machine_name, machine_username, machine_password)

        self.machine_type = 'aws'
        self.instance_id = instance_id
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region = region
        self.bucket_name = 'dxlauto-bucket'

        self.ec2_resource = boto3.resource('ec2',
                                           aws_access_key_id=self.access_key_id,
                                           aws_secret_access_key=self.secret_access_key,
                                           region_name=self.region)

        self.ec2_client = boto3.client('ec2',
                                       aws_access_key_id=self.access_key_id,
                                       aws_secret_access_key=self.secret_access_key,
                                       region_name=self.region)
        self.ec2_ssm_client = boto3.client('ssm',
                                           aws_access_key_id=self.access_key_id,
                                           aws_secret_access_key=self.secret_access_key,
                                           region_name=self.region)
        self.s3_client = boto3.client('s3',
                               aws_access_key_id=self.access_key_id,
                               aws_secret_access_key=self.secret_access_key,
                               region_name=self.region)
        self.s3_resource = boto3.resource('s3',
                                          aws_access_key_id=self.access_key_id,
                                          aws_secret_access_key=self.secret_access_key,
                                          region_name=self.region)
        aws_region_list = ['us-west-1', 'us-west-2', 'ca-central-1', 'eu-west-1', 'eu-west-2', 'eu-central-1',
                           'ap-south-1', 'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
                           'sa-east-1', 'sa-east-2']

        # setup logging - change level to DEBUG to view all the activity
        self.logger = logging.getLogger(__name__)
        formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s', datefmt="%Y%m%d-%H%M%S")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.debug("Instance {0} init done".format(self.instance_id))

        # Store instance
        self.instance = self.ec2_resource.Instance(self.instance_id)

        # Configure to use AWS CLI on the instance
        self.configure_aws_cli(access_key_id, secret_access_key, region)

        # create bucket folder for machine upload/download
        response = self.s3_client.list_buckets()
        bucket_list = [bucket['Name'] for bucket in response['Buckets']]
        self.logger.debug(bucket_list)
        if self.bucket_name not in bucket_list:
            #self.s3.create_bucket(Bucket=self.bucket_name, CreateBucketConfiguration=CreateBucketConfiguration)
            bucket_created = False
            for region in aws_region_list:
                try:
                    self.logger.debug("Trying to create bucket in region: {}".format(region))
                    bucket_config = {'LocationConstraint': region}
                    self.s3_client.create_bucket(Bucket=self.bucket_name, CreateBucketConfiguration=bucket_config)
                    bucket_created = True
                    break
                except botocore.exceptions.ClientError:
                    self.logger.error("Unable to create bucket in region: {}".format(region))
                    continue
            if not bucket_created:
                raise Exception, "ERROR: Unable to create bucket in any of the regions: {}".format(aws_region_list)
        # create bucket folder for machine
        print self.s3_client.put_object(Bucket=self.bucket_name, Key=instance_id+'/')

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
        return self.instance.public_ip_address

    @property
    def name(self):
        return self.instance.public_dns_name

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
        try:
            self.execute_command("ls {}".format(file_path), timeout=2)
            return True
        except TimeoutError as ex:
            self.logger.debug("File {} does not exist!".format(file_path))
            return False

    def check_folder_exists(self, folder_path):
        """
        check if the folder exists on remote machine
        :param folder_path: path on the remote machine
        :return: True/False
        """
        try:
            self.execute_command("ls {}".format(folder_path), timeout=2)
            return True
        except TimeoutError as ex:
            self.logger.debug("Folder {} does not exist!".format(folder_path))
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
        """
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
        """

    def download_folder(self, local_destination, remote_destination):
        """
        download folder from remote destination to local destination
        :param local_destination: path of folder on local machine
        :param remote_destination: path of folder on remote machine
        :return: true/false
        """
        self.logger.debug("Downloading folder FROM={}, TO={}".format(remote_destination, local_destination))
        """
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
        self.logger.debug("Uploading file {0} FROM={1}, TO={2}".format(file_name, local_destination, remote_destination))
        local_file_path=os.path.join(local_destination, file_name)
        # check local file exists
        if not os.path.exists(local_file_path):
            self.logger.error("No file exists in local machine at path {}!".format(local_file_path))
            return False
        # check remote path exists
        if not self.check_folder_exists(remote_destination):
            self.logger.debug("No folder exists in remote machine at path {}!".format(remote_destination))
            self._mkdir_path(remote_destination)
        uploaded_file = self.instance_id+'/'+file_name
        bucket_path = self.bucket_name+'/'+self.instance_id
        # upload file to bucket
        self.s3_resource.meta.client.upload_file(local_file_path, self.bucket_name, uploaded_file)
        # sync file to machine from bucket
        self.execute_command("sudo aws s3 sync s3://{0} {1} --exclude \"*\" --include \"{2}\"".format(bucket_path, remote_destination, file_name))
        return self.check_file_exists(os.path.join(remote_destination, file_name))

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
            self.logger.error("No folder exists in local machine at path {}!".format(local_destination))
            return False
        # check remote path exists
        if not self.check_folder_exists(remote_destination):
            self.logger.debug("No folder exists in remote machine at path {}!".format(remote_destination))
            self._mkdir_path(remote_destination)

        bucket_path = self.bucket_name+'/'+self.instance_id
        for file_name in os.listdir(local_destination):
            local_file_path=os.path.join(local_destination, file_name)
            uploaded_file = self.instance_id+'/'+file_name
            # upload file to bucket
            self.s3_resource.meta.client.upload_file(local_file_path, self.bucket_name, uploaded_file)
            # sync file to machine from bucket
            self.execute_command("sudo aws s3 sync s3://{0} {1} --exclude \"*\" --include \"{2}\"".format(bucket_path, remote_destination, file_name))
            if not self.check_file_exists(os.path.join(remote_destination, file_name)):
                self.logger.error("Problem while uploading file {}!".format(os.path.join(local_destination, file_name)))
                return False
        return True
        """
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
        try:
            output = self.execute_command("service {} status".format(service_name), timeout=10)
            if not output:
                self.logger.debug("No service found with name '{}'!".format(service_name))
                return None
            if 'stopped' in output:
                self.logger.debug("Service '{}' is not running".format(service_name))
                return False
            if 'running' in output:
                self.logger.debug("Service '{}' is running".format(service_name))
                return True
        except TimeoutError as ex:
            self.logger.debug("Service '{}' is not running".format(service_name))
            return False

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

    def execute_command(self, command, timeout=10):
        """
        execute command on remote machine
        :param command: command to execute on remote machine
        :param timeout: timeout
        :return: output of command execution
        """
        self.logger.debug("Executing Command: '{}'".format(command))
        cmd = [command]
        command_meta = self.ec2_ssm_client.send_command(DocumentName="AWS-RunShellScript", Parameters={'commands': cmd},
                                                        InstanceIds=[self.instance_id])
        time_initial = time.time()
        now = time.time()
        while now - time_initial < timeout:
            command_status = self.ec2_ssm_client.list_commands(CommandId=
                                                               command_meta["Command"]["CommandId"])["Commands"][0]["Status"]
            if command_status == "Success":
                command_result = self.ec2_ssm_client.get_command_invocation(InstanceId=self.instance_id,
                                                                            CommandId=command_meta["Command"]["CommandId"])["StandardOutputContent"]
                self.logger.debug("Command Output: '{}'".format(command_result))
                return command_result
            else:
                time.sleep(0.1)
                now = time.time()
        if now - time_initial > timeout:
            command_status = self.ec2_ssm_client.list_commands(CommandId=
                                                               command_meta["Command"]["CommandId"])["Commands"][0]["Status"]
            self.logger.debug("Command Status = {0}".format(command_status))
            if command_status != "Success":
                raise TimeoutError, "function timed out"

    # this method does not work properly - suggest using sync method for async/sync both
    def execute_command_async(self, command):
        """
        execute command on remote machine asynchronously
        :param command: command to execute on remote machine
        :return: output of command execution
        """
        cmd = [command]
        self.ec2_ssm_client.send_command(DocumentName="AWS-RunShellScript", Parameters={'commands': cmd},
                                           InstanceIds=[self.instance_id])


    # --------------------------------------------------
    # UTILS
    # --------------------------------------------------

    def _mkdir_path(self, remote_directory):
        """
        makes the directory tree recursively, if it does not exist
        :param remote_directory:
        :return: None
        """
        self.logger.debug("remote directory = {}".format(remote_directory))
        directory_tree = remote_directory.split('/')
        directory_tree = directory_tree[1:len(directory_tree)-1]
        for tree_depth in range(1, len(directory_tree)):
            self.logger.debug("depth={}".format(tree_depth))
            self.logger.debug("DT={}".format(directory_tree))
            self.logger.debug("DT_sub={}".format(directory_tree[:tree_depth]))
            sub_tree = '/'.join(directory_tree[:tree_depth])
            self.logger.debug("ST={}".format(sub_tree))
            if not self.check_folder_exists("/{}/".format(sub_tree)):
                self.execute_command("sudo mkdir /{}/".format(sub_tree), timeout=5)

    def configure_aws_cli(self, access_key_id, secret_access_key, region):
        """
        configure AWS environment to be able to execute CLI commands
        :param access_key_id:
        :param secret_access_key:
        :param region:
        :return:
        """
        self.execute_command("export AWS_ACCESS_KEY_ID={}".format(access_key_id), timeout=5)
        self.execute_command("export AWS_SECRET_ACCESS_KEY={}".format(secret_access_key), timeout=5)
        self.execute_command("export AWS_DEFAULT_REGION={}".format(region), timeout=5)


# --------------------------------------------------
#  CUSTOM EXCEPTIONS
# --------------------------------------------------

class TimeoutError(Exception):
    pass
