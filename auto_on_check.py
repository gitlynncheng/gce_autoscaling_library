import time
import google.auth
from pprint import pprint
from googleapiclient import discovery
from google.oauth2 import service_account
from oauth2client.client import GoogleCredentials
from google.cloud import monitoring_v3


credentials = service_account.Credentials.from_service_account_file("xxxxx.json")
service = discovery.build('compute', 'v1', credentials=credentials)
client = monitoring_v3.MetricServiceClient(credentials=credentials)

# Project ID for this request.
project = '<<project_name>>' 
# Name of the zone for this request.
zone = 'asia-east1-b'
# autoscaling instance
instance_group_manager = 'lynn-www3-mig'  
# 檢查用的 instance_name 與 上限值
check_instance = 'lynn-www2'
check_threshold = 0.01

print("Start auto_on_check.py")

def autoscaler_on():
    # 取得物件get_alert_policy的值
    policy_value = get_alert_policy()
    #print("policy_value # ",policy_value,policy_value[0])

    # autoscaler 資訊取得
    request = service.autoscalers().get(project=project, zone=zone, autoscaler=instance_group_manager)
    response = request.execute()
    #print("## Get Instance group :\n",response)
    #print("## Response status : ",response['autoscalingPolicy']['mode'])

    # 判斷式
    # # autoscaling mode = off 且 檢查用的主機大於上限值時 執行 ON
    # # 其他狀況 不動作 
    if response['autoscalingPolicy']['mode'] == 'OFF' and policy_value[0] > check_threshold:
        autoscaler_body = {
            "name": f"{instance_group_manager}",
            "target": f"projects/{project}/zones/{zone}/instanceGroupManagers/{instance_group_manager}",
            "autoscalingPolicy": {
                "minNumReplicas": 0,
                "maxNumReplicas": 3,
                "mode": "on"
            }
            
        }

        #print(autoscaler_body)
        # update Autoscaling
        request = service.autoscalers().update(project=project, zone=zone, body=autoscaler_body)
        response = request.execute()
        #pprint(response)
        print("## Autoscaling On Success!\n")

    else :
        print(f"## Status : {response['autoscalingPolicy']['mode']}")
        print(f"## Threshold : {check_threshold} ")
        print(f"## Policy Value 0 : {policy_value[0]} ")


def get_alert_policy():
    policy_value = []
    project_name = f"projects/{project}"
    interval = monitoring_v3.TimeInterval()

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10 ** 9)
    interval = monitoring_v3.TimeInterval(
        {
            "end_time": {"seconds": seconds, "nanos": nanos},
            "start_time": {"seconds": (seconds - 600), "nanos": nanos}, # 10 min
        }
    )
    aggregation = monitoring_v3.Aggregation(
        {
            "alignment_period": {"seconds": 300},  # 5 minutes
            "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
        }
    )
    results = client.list_time_series(
        request={
            "name": project_name,
            "filter": f'metric.type = "compute.googleapis.com/instance/cpu/utilization" AND (metric.labels.instance_name = {check_instance})',
            "interval": interval,
            "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            "aggregation": aggregation,
        }
    )
    
    for result in results:
        #v = 1
        for value in result.points :
            #print(v,"$ ", value)
            #v += 1
            #print(value.value.double_value)
            policy_value.append(value.value.double_value)
    return (policy_value)

autoscaler_on()

