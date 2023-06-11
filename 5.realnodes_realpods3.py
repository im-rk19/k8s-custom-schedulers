from kubernetes import client, config, watch


def nodes_available():
    api = client.CoreV1Api()
    nodes = api.list_node().items
    available_nodes = []

    for node in nodes:
        cpu_allocatable = int(node.status.allocatable['cpu'])
        memory_allocatable = int(node.status.allocatable['memory'][:-2])  # Remove the 'Ki' suffix
        cpu_utilization = int(node.status.capacity['cpu']) - cpu_allocatable  # Calculate remaining CPU
        memory_utilization = int(node.status.capacity['memory'][:-2]) - memory_allocatable  # Calculate remaining memory

        available_nodes.append({'name': node.metadata.name, 'cpu_allocatable': cpu_allocatable,
                                'memory_allocatable': memory_allocatable, 'cpu_remaining': cpu_utilization,
                                'memory_remaining': memory_utilization})

    return available_nodes


def calculate_score(node, cpu_utilization, memory_utilization):
    uc = node['cpu_remaining'] - cpu_utilization
    um = node['memory_remaining'] - memory_utilization
    score = (cpu_utilization * uc + memory_utilization * um) / (uc + um)
    return score


def scheduler(pod, available_nodes):
    api = client.CoreV1Api()
    cpu_utilization = sum(node['cpu_allocatable'] for node in available_nodes)
    memory_utilization = sum(node['memory_allocatable'] for node in available_nodes)

    scores = []
    for node in available_nodes:
        score = calculate_score(node, cpu_utilization, memory_utilization)
        scores.append({'name': node['name'], 'cpu_allocatable': node['cpu_allocatable'], 'memory_allocatable': node['memory_allocatable'], 'score': score})

    sorted_nodes = sorted(scores, key=lambda x: x['score'], reverse=True)

    for node in sorted_nodes:
        if node['cpu_allocatable']*1000 >= pod['cpu_required'] and node['memory_allocatable']*1000 >= pod['memory_required']:
            # Calculate remaining resources after scheduling
            remaining_cpu = (node['cpu_allocatable'] - pod['cpu_required'] * 1000) / 1000  # Convert milliCPU to CPU
            remaining_memory = node['memory_allocatable'] - pod['memory_required']

            target = client.V1ObjectReference(
                kind="Node",
                api_version="v1",
                name=node['name'],
                namespace=pod['namespace']
            )
            metadata = client.V1ObjectMeta(name=pod['name'])
            body = client.V1Binding(target=target, metadata=metadata)

            try:
                api.create_namespaced_binding(namespace=pod['namespace'], body=body)
                return node['name'], remaining_cpu, remaining_memory
            except client.rest.ApiException as e:
                print(f"Error binding {pod['name']}: {e}")

    return None, None, None  #nodename, remaining_cpu, remaining_memory


def main():
    config.load_kube_config()
    api = client.CoreV1Api()

    print("Available Nodes:")
    available_nodes = nodes_available()
    for node in available_nodes:
        print(f"{node['name']}: {node['cpu_allocatable']} CPUs, {node['memory_allocatable']} Memory")

    w = watch.Watch()
    for event in w.stream(api.list_pod_for_all_namespaces):
        pod = event['object']

        if pod.status.phase == "Pending" and pod.spec.scheduler_name == "scheduler":
            pod_data = {
                'name': pod.metadata.name,
                'namespace': pod.metadata.namespace,
                'cpu_required': int(pod.spec.containers[0].resources.requests['cpu'][:-1]),
                'memory_required': int(pod.spec.containers[0].resources.requests['memory'][:-2])
            }

            node_name, remaining_cpu, remaining_memory = scheduler(pod_data, available_nodes)
            if node_name:
                print(f"Scheduled {pod_data['name']} on {node_name}")
                print(f"Remaining CPU: {remaining_cpu} CPUs")
                print(f"Remaining Memory: {remaining_memory} MiB")
            else:
                print(f"No node can accommodate {pod_data['name']}")


if __name__ == '__main__':
    main()
