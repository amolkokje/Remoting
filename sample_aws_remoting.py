import os, sys, re, threading, subprocess, win32api, time
from string import ascii_uppercase
import ConfigParser
import boto3

from AwsLinuxRemoteMachine import AwsLinuxRemoteMachine

try:
    from dxlclient.client import DxlClient
    from dxlclient.client_config import DxlClientConfig
    from dxlclient.broker import Broker
    from dxlclient.message import Event
    from dxlclient.callbacks import EventCallback
    from dxlclient.callbacks import RequestCallback
    from dxlclient.client import DxlClient
    from dxlclient.message import Message, Request, Response
    from dxlclient.service import ServiceRegistrationInfo
    from threading import Condition
    from dxlclient.callbacks import EventCallback
    from dxlclient.callbacks import ResponseCallback
    from dxlclient.client import DxlClient
    from dxlclient.client_config import DxlClientConfig
    from dxlclient.message import Event
except:
    pass


config_file = "C:\\Users\\aakokje\\Automation_Tools\\Automation_Tools\\Remote_Machine\\aws.ini"
Config = ConfigParser.ConfigParser()
Config.read(config_file)
user_access_key_id = Config.get('MAIN', 'access_key_id')
user_secret_access_key = Config.get('MAIN', 'secret_access_key')
region = Config.get('MAIN', 'region')
key_name = Config.get('MAIN', 'key_name')
print "{}, {}, {}".format(user_access_key_id, user_secret_access_key, region)


# create machine instance
dxlbroker_image_id = 'ami-f7c5ec92'
#aws_machine = AwsLinuxRemoteMachine.create_aws_linux_machine(dxlbroker_image_id, user_access_key_id,
#                                                             user_secret_access_key, region)

# get handle to the machine instance
instance_id = 'i-0044687d03b3c9d27'
aws_machine = AwsLinuxRemoteMachine(instance_id, user_access_key_id, user_secret_access_key, region, log_level='DEBUG')

print "TEST: UPLOAD FILE, FOLDER"
#aws_machine.upload_file("C:\\temp_aa", "/tmp/upload_file/", "a2.txt")
#aws_machine.upload_folder("C:\\temp_aa", "/tmp/upload_folder/")

# STEP-2: check dxlbroker running - stop, start
print "TEST: SERVICE START, STOP, STATUS"
#aws_machine.execute_command("service dxlbroker start", timeout=30)
#print "dxlbroker service status = {}".format(aws_machine.service_status('dxlbroker'))
#aws_machine.execute_command("service dxlbroker stop")
#print "dxlbroker service status = {}".format(aws_machine.service_status('dxlbroker'))
#aws_machine.execute_command("service dxlbroker start", timeout=30)
#print "dxlbroker service status = {}".format(aws_machine.service_status('dxlbroker'))

# STEP-3: check file and folder structure
print "TEST: FILE, FOLDER STRUCTURE"
#print "FOLDER EXISTS = {}".format(aws_machine.check_folder_exists('/var/McAfee/dxlbroker/keystore/'))
#print "FILE EXISTS = {}".format(aws_machine.check_file_exists('/var/McAfee/dxlbroker/keystore/broker.crt'))
#print "FOLDER EXISTS = {}".format(aws_machine.check_folder_exists('/var/McAfee/dxlbroker/keystore2/'))
#print "FILE EXISTS = {}".format(aws_machine.check_file_exists('/var/McAfee/dxlbroker/keystore/broker2.crt'))

# STEP-4: connect python client (need SG with rule for port 8883: "Custom TCP Rule | TCP | 8883 | 0.0.0.0/0")
print "TEST: PYTHON CLIENT"
brokerCaBundle = "C:\\test\\dxlbroker_install_files\\keystore\\ca-broker.crt"
certFile = "C:\\test\\dxlbroker_install_files\\keystore\\broker.crt"
privateKey = "C:\\test\\dxlbroker_install_files\\keystore\\broker.key"
brokerString = "ssl://{}".format(aws_machine.ip)
action = "publish_event"
topic = "/mcafee/client/controlevent"
config = DxlClientConfig(
    broker_ca_bundle=brokerCaBundle,
    cert_file=certFile,
    private_key=privateKey,
    brokers=[Broker.parse(brokerString)])

with DxlClient(config) as dxl_client:
    # Connect to the fabric
    dxl_client.connect()
    if dxl_client.connected:
        print "Connected ... \n"
    else:
        print "Not Connected ... \n"

    sleepTime = 1
    rb = os.urandom(100)
    event = Event(str(topic))
    event.payload = rb
    print "payload={}".format(rb)
    topic.encode('ascii', 'ignore')
    dxl_client.send_event(event)

    # Connect to the fabric
    dxl_client.disconnect()
    if dxl_client.connected:
        print "Connected ... \n"
    else:
        print "Not Connected ... \n"
