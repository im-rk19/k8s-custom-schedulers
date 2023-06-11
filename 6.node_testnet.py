from kubernetes import client, config, watch

#int(node.status.allocatable['cpu_usage'])

config.load_kube_config()
api = client.CoreV1Api()
nodes = api.list_node().items
available_nodes = []

def nodes_available():
    api = client.CoreV1Api()
    nodes = api.list_node().items
    available_nodes = []

    for node in nodes:
        cpu_allocatable = int(node.status.allocatable['cpu'])  # Convert to milliCPU
        memory_allocatable = int(node.status.allocatable['memory'][:-2])  # Remove the 'Ki' suffix

        # Calculate CPU usage of the node
        cpu_usage = 0
        for condition in node.status.conditions:
            if condition.type == 'Ready' and condition.status == 'True':
                for metric in condition.metrics:
                    if metric.type == 'Resource':
                        for usage in metric.resource_usage:
                            if usage.name == 'cpu':
                                cpu_usage = int(usage.value)
                                break

        cpu_remaining = cpu_allocatable - cpu_usage

        available_nodes.append({
            'name': node.metadata.name,
            'cpu_allocatable': cpu_allocatable,
            'memory_allocatable': memory_allocatable,
            'cpu_remaining': cpu_remaining
        })

    return available_nodes


def main():
    a = nodes_available()
    print("---------------------------------")
    print(a)


if __name__ == '__main__':
    main()
