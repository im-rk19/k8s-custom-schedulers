#for affinity use nginx backend and frontend find....maybe mongodb (backend) in one pod and mongoexpress (frontend) then make both have affinity
#nginx and mysql also we can try for other 2 pods maybe
#use nana example for this scheduling since mongodb and mongoexpress are part of same application

#basically hardcording so we dont need to code for switch and all
from kubernetes import client, config
import random

def nodes_available(client):
    nodes = client.list_node().items
    available_nodes = []

    for node in nodes:
        cpu_allocatable = int(node.status.allocatable['cpu']) * 1000  # milliCPU
        memory_allocatable = int(node.status.allocatable['memory'][:-2])  # Remove the 'Ki' suffix
        pods = client.list_pod_for_all_namespaces(field_selector='spec.nodeName={}'.format(node.metadata.name)).items

        cpu_request_sum = 0
        memory_request_sum = 0 

        for pod in pods:
            try:
                cpu_request = pod.spec.containers[0].resources.requests['cpu']
                if cpu_request is None:
                    continue
                cpu_request_sum += int(cpu_request[:-1])
            except (TypeError, KeyError):
                continue

        for pod in pods:
            try:
                memory_request = pod.spec.containers[0].resources.requests['memory']
                if memory_request is None:
                    continue
                memory_request_sum += int(memory_request[:-2])
            except (TypeError, KeyError):
                continue
        
        cpu_utilization = cpu_allocatable - cpu_request_sum
        memory_utilization = memory_allocatable - memory_request_sum
    
        available_nodes.append({
            'name': node.metadata.name,
            'cpu_allocatable': cpu_allocatable,
            'memory_allocatable': memory_allocatable,
            'cpu_usage': cpu_request_sum,
            'memory_usage': memory_request_sum,
            'cpu_remaining': cpu_utilization,
            'memory_remaining': memory_utilization
        })

    return available_nodes

def distance_matrix(nodes):
    distance_scores = {}
    for node1 in nodes:
        for node2 in nodes:
            if node1 != node2:
                distance = random.randint(1, 10)  # Random distance value
                distance_scores[(node1['name'], node2['name'])] = distance

    return distance_scores

def calculate_score(node, cpu_utilization, memory_utilization):
    cpu_remaining = node['cpu_remaining']
    memory_remaining = node['memory_remaining']
    uc = cpu_utilization
    um = memory_utilization
    score = ((cpu_remaining * uc) + (memory_remaining * um)) / (uc + um)
    return score

def total_score(cpu_memory_score, distance_score):
    # Calculate the total score by combining cpu_memory_score and distance_score; weightage to be 50:50
    total_scores = {}

    for node, score in cpu_memory_score.items():
        distance = distance_score[node]
        total_scores[node] = score + distance

    return total_scores

def check_inter_pod_affinity(pod, scheduled_pods):
    # Check for inter-pod affinity rules for the given pod
    # Implement the logic for pod affinity checks
    # Return True if the pod satisfies the affinity rules, False otherwise
    return True

def scheduler(pod, available_nodes, cpu_utilization, memory_utilization):
    scores = []
    for node in available_nodes:
        score = calculate_score(node, cpu_utilization, memory_utilization)
        scores.append({'name': node['name'], 'cpu_allocatable': node['cpu_allocatable'], 'memory_allocatable': node['memory_allocatable'], 'score': score})

    sorted_nodes = sorted(scores, key=lambda x: x['score'], reverse=True)

    for node in sorted_nodes:
        if node['cpu_allocatable']*1000 >= pod['cpu_required'] and node['memory_allocatable']*1000 >= pod['memory_required']:
            remaining_cpu = (node['cpu_allocatable'] - pod['cpu_required'] * 1000) / 1000
            remaining_memory = node['memory_allocatable'] - pod['memory_required']

            return node['name'], remaining_cpu, remaining_memory

    return None, None, None

def main():
    config.load_kube_config()
    k8s_client = client.CoreV1Api()
    available_nodes = nodes_available(k8s_client)
    distance_scores = distance_matrix(available_nodes)
    print(available_nodes)
    print(distance_scores)
    scheduled_pods = []
    total_pods = 0  # Replace with the actual number of pods

    cpu_utilization = sum(node['cpu_allocatable'] for node in available_nodes)
    memory_utilization = sum(node['memory_allocatable'] for node in available_nodes)

    while True:
        # Retrieve a pod that needs to be scheduled
        pod = {}  # Replace with actual pod details

        # Apply affinity checks using check_inter_pod_affinity
        if check_inter_pod_affinity(pod, scheduled_pods):
            node_name, remaining_cpu, remaining_memory = scheduler(pod, available_nodes, cpu_utilization, memory_utilization)
            if node_name:
                # Schedule the pod to the selected node
                # Update the scores and scheduled pods list

                # Adjust cpu_utilization and memory_utilization

                # Break the loop if all pods are scheduled
                if len(scheduled_pods) == total_pods:
                    break

    # Print the final scheduled pods
    print("Scheduled pods:")
    for pod in scheduled_pods:
        print(pod)

if __name__ == '__main__':
    main()
