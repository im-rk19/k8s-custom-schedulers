from kubernetes import client, config


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

    ###print(cpu_utilization)  
    ###print(memory_utilization)
    ###print(node['cpu_allocatable'])

    scores = []
    for node in available_nodes:
        score = calculate_score(node, cpu_utilization, memory_utilization)
        scores.append({'name': node['name'], 'cpu_allocatable': node['cpu_allocatable'], 'memory_allocatable': node['memory_allocatable'], 'score': score})


    # Sort nodes by score in descending order
    sorted_nodes = sorted(scores, key=lambda x: x['score'], reverse=True)

    print(sorted_nodes)
    # Find the first node that can accommodate the pod
    for node in sorted_nodes:
        if node['cpu_allocatable'] >= pod['cpu_required'] and node['memory_allocatable'] >= pod['memory_required']:
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

    # Define test pods
    test_pods = [
        {
            'name': 'pod1',
            'cpu_required': 1,
            'memory_required': 1024  # Memory in MiB
        },
        {
            'name': 'pod2',
            'cpu_required': 2,
            'memory_required': 2048  # Memory in MiB
        }
    ]

    # Schedule pods
    for pod in test_pods:
        """node_name = scheduler(pod, available_nodes)
        if node_name:
            print(f"Scheduled {pod['name']} on {node_name}")
        else:
            print(f"No node can accommodate {pod['name']}")
        """
        node_name = scheduler(pod, available_nodes)
        if node_name:
            # Find the scheduled node
            scheduled_node = next(node for node in available_nodes if node['name'] == node_name)

            # Calculate remaining CPU and memory after scheduling
            remaining_cpu = scheduled_node['cpu_allocatable'] - pod['cpu_required']
            remaining_memory = scheduled_node['memory_allocatable'] - pod['memory_required']

            print(f"Scheduled {pod['name']} on {node_name}")
            print(f"Remaining CPU: {remaining_cpu} CPUs")
            print(f"Remaining Memory: {remaining_memory} MiB")
        else:
            print(f"No node can accommodate {pod['name']}")


if __name__ == '__main__':
    main()

