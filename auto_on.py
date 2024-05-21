
import time
import google.auth
from pprint import pprint
from googleapiclient import discovery
from google.oauth2 import service_account
from oauth2client.client import GoogleCredentials


credentials = service_account.Credentials.from_service_account_file("xxxxx.json")
service = discovery.build('compute', 'v1', credentials=credentials)


# Project ID for this request.
project = '<<project_name>>' 
# Name of the zone for this request.
zone = 'asia-east1-b'
# The name of the managed instance group.
instance_group_manager = 'lynn-www3-mig'  



def autoscaler_on():
    request = service.autoscalers().get(project=project, zone=zone, autoscaler=instance_group_manager)
    response = request.execute()

    print("## Get Instance group :\n",response)
    print("## Response status : ",response['autoscalingPolicy']['mode'])
    if response['autoscalingPolicy']['mode'] == 'OFF' :
        autoscaler_body = {
        "name": f"{instance_group_manager}",
        "target": f"projects/{project}/zones/{zone}/instanceGroupManagers/{instance_group_manager}",
        "autoscalingPolicy": {
            "minNumReplicas": 0,
            "maxNumReplicas": 3,
            "mode": "on"
        }
        
        }

        print(autoscaler_body)
        request = service.autoscalers().update(project=project, zone=zone, body=autoscaler_body)
        response = request.execute()

        pprint(response)
        print("## Autoscaling On Success!\n")
    elif response['autoscalingPolicy']['mode'] == 'ON':
        print("## Already on")




autoscaler_on()

