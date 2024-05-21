import time
from pprint import pprint
from googleapiclient import discovery
from google.oauth2 import service_account
from google.cloud import monitoring_v3

credentials = service_account.Credentials.from_service_account_file("xxxxx.json")
service = discovery.build('compute', 'v1', credentials=credentials)
client = monitoring_v3.MetricServiceClient(credentials=credentials)

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
# 檢查用的 instance_name 與 下限值
check_instance = 'lynn-www2'
check_threshold = 0.2
print("Start auto_off_check.py")

def autoscaler_off():
    # 取得物件get_alert_policy的值
    policy_value = get_alert_policy()
    #print("policy_value # ",policy_value,policy_value[0])

    # autoscaler 資訊取得
    request = service.autoscalers().get(project=project, zone=zone, autoscaler=instance_group_manager)
    response = request.execute()
    #print("Get Instance group :\n",response)
    #print("Response status : ",response['autoscalingPolicy']['mode'])

    # 判斷式
    # # autoscaling mode = ON 且 檢查用的主機小於下限值時 執行 OFF
    # # 其他狀況 不動作 
    if response['autoscalingPolicy']['mode'] == 'ON' and policy_value[0] < check_threshold:
        autoscaler_body = {
            "name": f"{instance_group_manager}",
            "target": f"projects/{project}/zones/{zone}/instanceGroupManagers/{instance_group_manager}",
            "autoscalingPolicy": {
                "minNumReplicas": 0,
                "maxNumReplicas": 3,
                "mode": "OFF"
            }
        }

        #print(autoscaler_body)
        request = service.autoscalers().update(project=project, zone=zone, body=autoscaler_body)
        response = request.execute()
        #pprint(response)
        print("### Autoscaling Off Success!\n")
        time.sleep(10)
        instance_size()

    else :
        print(f"## Status : {response['autoscalingPolicy']['mode']}")
        print(f"## Threshold : {check_threshold} ")
        print(f"## Policy Value 0 : {policy_value[0]} ")


def instance_size():
    request = service.instanceGroupManagers().resize(project=project, zone=zone, instanceGroupManager=instance_group_manager, size=size)
    response = request.execute()
    print(response)
    print("### Instance resize Success!\n")


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
        v = 1
        for value in result.points :
            #print(v,"$ ", value)
            v += 1
            #print(value.value.double_value)
            policy_value.append(value.value.double_value)
    return (policy_value)


autoscaler_off()


