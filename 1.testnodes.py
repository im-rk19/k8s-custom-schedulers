import random


def nodes_available():
    nodes = [
        {'name': 'node1', 'cpu': 2, 'memory': 8},
        {'name': 'node2', 'cpu': 3, 'memory': 12},
        {'name': 'node3', 'cpu': 4, 'memory': 16},
        {'name': 'node4', 'cpu': 1, 'memory': 4},
        {'name': 'node5', 'cpu': 2, 'memory': 8},
        {'name': 'node6', 'cpu': 3, 'memory': 12},
        {'name': 'node7', 'cpu': 4, 'memory': 16},
        {'name': 'node8', 'cpu': 1, 'memory': 4}
    ]

    cpu_utilization = sum(node['cpu'] for node in nodes)
    memory_utilization = sum(node['memory'] for node in nodes)

    return nodes, cpu_utilization, memory_utilization


def pod_cpu_memory_requirement():
    pods = [
        {'name': 'pod1', 'cpu': 2, 'memory': 4},
        {'name': 'pod2', 'cpu': 1, 'memory': 8}
    ]

    return pods


def calculate_score(node, cpu_utilization, memory_utilization):
    uc = node['cpu']
    um = node['memory']
    score = ((cpu_utilization * uc) + (memory_utilization * um)) / (cpu_utilization + memory_utilization)
    print(score)
    return score


def scheduler(pod, nodes, cpu_utilization, memory_utilization):
    scores = {}
    for node in nodes:
        score = calculate_score(node, cpu_utilization, memory_utilization)
        scores[node['name']] = score

    # Sort nodes by score in descending order
    sorted_nodes = sorted(nodes, key=lambda n: scores[n['name']], reverse=True)

    # Find the first node that can accommodate the pod
    for node in sorted_nodes:
        if node['cpu'] >= pod['cpu'] and node['memory'] >= pod['memory']:
            # Assign the pod to the node
            print(f"Scheduled {pod['name']} on {node['name']} with score {scores[node['name']]}")
            node['cpu'] -= pod['cpu']
            node['memory'] -= pod['memory']
            return True

    # No node can accommodate the pod
    return False


def main():
    nodes, cpu_utilization, memory_utilization = nodes_available()
    pods = pod_cpu_memory_requirement()

    for pod in pods:
        if not scheduler(pod, nodes, cpu_utilization, memory_utilization):
            print(f"No node can accommodate {pod['name']}")
        print()

if __name__ == '__main__':
    main()
