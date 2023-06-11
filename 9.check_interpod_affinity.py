def check_inter_pod_affinity(pod, scheduled_pods, node_name):
    if 'affinity' in pod and 'podAffinity' in pod['affinity']:
        pod_affinity = pod['affinity']['podAffinity']
        if 'requiredDuringSchedulingIgnoredDuringExecution' in pod_affinity:
            required_affinity = pod_affinity['requiredDuringSchedulingIgnoredDuringExecution']
            for selector in required_affinity['labelSelector']['matchExpressions']:
                if selector['key'] == 'app':
                    app_value = selector['values'][0]
                    for scheduled_pod in scheduled_pods:
                        if scheduled_pod['name'] != pod['name'] and scheduled_pod['node_name'] == node_name:
                            pod_labels = scheduled_pod['labels']
                            if 'app' in pod_labels and pod_labels['app'] == app_value:
                                return True
    return True  # No affinity rules specified, so consider it as satisfied

def main():
    a = check_inter_pod_affinity()
    print(a)


if __name__ == '__main__':
    main()
