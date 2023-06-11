from kubernetes import client, config, watch


def nodes_available():
    """
    Return a list of available nodes with their allocatable resources
    """
    api = client.CoreV1Api()

    nodes = api.list_node().items
    available_nodes = []

    for node in nodes:
        cpu_allocatable = int(node.status.allocatable['cpu'])
        memory_allocatable = int(node.status.allocatable['memory'][:-2])  # Remove the 'Ki' suffix
        available_nodes.append({'name': node.metadata.name, 'cpu_allocatable': cpu_allocatable, 'memory_allocatable': memory_allocatable})

    return available_nodes


def calculate_score(node, cpu_utilization, memory_utilization):
    """
    Calculate the score for a node based on CPU and memory utilization
    """
    uc = node['cpu_allocatable'] - cpu_utilization
    um = node['memory_allocatable'] - memory_utilization
    score = (cpu_utilization * uc + memory_utilization * um) / (uc + um)
    return score


def scheduler(pod, available_nodes):
    """
    Schedule a pod to a node based on the available resources and the score of each node
    """
    # Calculate the sum of CPU and memory utilization across all nodes
    cpu_utilization = sum(node['cpu_allocatable'] for node in available_nodes)
    memory_utilization = sum(node['memory_allocatable'] for node in available_nodes)

    scores = []
    for node in available_nodes:
        score = calculate_score(node, cpu_utilization, memory_utilization)
        scores.append({'name': node['name'], 'cpu_allocatable': node['cpu_allocatable'], 'memory_allocatable': node['memory_allocatable'], 'score': score})

    # Sort nodes by score in descending order
    sorted_nodes = sorted(scores, key=lambda x: x['score'], reverse=True)

    # Display scores and resources for each node
    print("Node Scores:")
    for node in sorted_nodes:
        print(f"Node: {node['name']}")
        print(f"CPU Allocatable: {node['cpu_allocatable']} CPUs")
        print(f"Memory Allocatable: {node['memory_allocatable']} MiB")
        print(f"Score: {node['score']}")
        print()

    # Find the first node that can accommodate the pod
    for node in sorted_nodes:
        if node['cpu_allocatable']*1000 >= pod['cpu_required'] and node['memory_allocatable']*1000 >= pod['memory_required']:
            return node['name']

    # No node can accommodate the pod
    return None


def main():
    # Load Kubernetes configuration
    config.load_kube_config()

    # Print available nodes
    available_nodes = nodes_available()
    print("Available Nodes:")
    for node in available_nodes:
        print(f"{node['name']}: {node['cpu_allocatable']} CPUs, {node['memory_allocatable']} Memory")

    # Watch for pod events
    api = client.CoreV1Api()
    w = watch.Watch()

    for event in w.stream(api.list_pod_for_all_namespaces):
        pod = event['object']

        if pod.spec.scheduler_name == "scheduler":
            cpu_required = int(pod.spec.containers[0].resources.requests['cpu'][:-1])  # Remove the 'm' suffix
            memory_required = int(pod.spec.containers[0].resources.requests['memory'][:-2])  # Remove the 'Mi' suffix

            pod_data = {
                'name': pod.metadata.name,
                'cpu_required': cpu_required,
                'memory_required': memory_required
            }

            node_name = scheduler(pod_data, available_nodes)
            print(node_name)
            if node_name:
                # Find the scheduled node
                scheduled_node = next(node for node in available_nodes if node['name'] == node_name)

                # Calculate remaining resources after scheduling
                remaining_cpu = (scheduled_node['cpu_allocatable'] - pod_data['cpu_required']) / 1000  # Convert milliCPU to CPU
                remaining_memory = scheduled_node['memory_allocatable'] - pod_data['memory_required']

                # Print scheduling details
                print(f"Scheduled {pod_data['name']} on {node_name}")
                print(f"Remaining CPU: {remaining_cpu} CPUs")
                print(f"Remaining Memory: {remaining_memory} MiB")
                print()

                # Create the binding
                body = client.V1Binding(
                    metadata=client.V1ObjectMeta(name=pod.metadata.name),
                    target=client.V1ObjectReference(kind="Node", api_version="v1", name=node_name),
                )
                api.create_namespaced_binding(namespace=pod.metadata.namespace, body=body)
            else:
                print(f"No node can accommodate {pod_data['name']}")
                print()

    w.stop()


if __name__ == '__main__':
    main()
