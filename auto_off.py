import time
from pprint import pprint
from googleapiclient import discovery
from google.oauth2 import service_account


credentials = service_account.Credentials.from_service_account_file("xxxxx.json")
service = discovery.build('compute', 'v1', credentials=credentials)


# Project ID for this request.
project = '<<project_name>>' 
# Name of the zone for this request.
zone = 'asia-east1-b'
# The name of the managed instance group.
instance_group_manager = 'lynn-www3-mig'  
# The number of running instances that the managed instance group should maintain at any given time.
# The group automatically adds or removes instances to maintain the number of instances specified by
# this parameter.
size = 0  

def autoscaler_off():
    request = service.autoscalers().get(project=project, zone=zone, autoscaler=instance_group_manager)
    response = request.execute()

    print("Get Instance group :\n",response)
    print("Response status : ",response['autoscalingPolicy']['mode'])
    if response['autoscalingPolicy']['mode'] == 'ON' :
        autoscaler_body = {
            "name": f"{instance_group_manager}",
            "target": f"projects/{project}/zones/{zone}/instanceGroupManagers/{instance_group_manager}",
            "autoscalingPolicy": {
                "minNumReplicas": 0,
                "maxNumReplicas": 3,
                "mode": "OFF"
            }
        }

        print(autoscaler_body)
        request = service.autoscalers().update(project=project, zone=zone, body=autoscaler_body)
        response = request.execute()
        pprint(response)
        print("### Autoscaling Off Success!\n")
        time.sleep(10)
        instance_size()
    elif response['autoscalingPolicy']['mode'] == 'OFF':
        print("## Already OFF")
        

def instance_size():
    request = service.instanceGroupManagers().resize(project=project, zone=zone, instanceGroupManager=instance_group_manager, size=size)
    response = request.execute()
    pprint(response)
    print("### Instance resize Success!\n")



autoscaler_off()


