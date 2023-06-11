from kubernetes import client, config
from datetime import datetime, timedelta

config.load_kube_config()

import kubernetes


def nodes_available(client):
    """Gets a list of all the nodes in the cluster and their available resources."""
    nodes = client.list_node().items
    available_nodes = []

    for node in nodes:
        cpu_allocatable = int(node.status.allocatable['cpu']) * 1000  #milliCPU
        memory_allocatable = int(node.status.allocatable['memory'][:-2])  # Remove the 'Ki' suffix
        #pods = client.list_namespaced_pod(namespace='default', field_selector='spec.nodeName={}'.format(node.metadata.name)).items
        pods = client.list_pod_for_all_namespaces(field_selector='spec.nodeName={}'.format(node.metadata.name)).items

        #print("pods are:")
        #print(pods)

        cpu_request_sum = 0
        memory_request_sum = 0 

        for pod in pods:
            try:
                cpu_request = pod.spec.containers[0].resources.requests['cpu']
                if cpu_request is None:
                    continue  # Skip the current iteration if cpu_request is None
                    # Process the non-None cpu_request here
                print(cpu_request)
                cpu_request_sum = cpu_request_sum + int(pod.spec.containers[0].resources.requests['cpu'][:-1])
                #print(cpu_request_sum)
        # ...
            except TypeError:
               continue  # Skip the current iteration if TypeError occurs
            except KeyError:
                continue  # Skip the current iteration if KeyError occurs
        
        
        for pod in pods:
            try:
                memory_request = pod.spec.containers[0].resources.requests['memory']
                #memory_request = pod.spec.containers[0].resources.requests.get('memory', '0')

                if memory_request is None:
                    continue  # Skip the current iteration if memory_request is None
                    # Process the non-None memory_request here
                print(memory_request)
                memory_request_sum = memory_request_sum + int(pod.spec.containers[0].resources.requests['memory'][:-2])
                #print("memory_request_sum = " + memory_request_sum)        
        # ...
            except TypeError:
               continue  # Skip the current iteration if TypeError occurs
            except KeyError:
                continue  # Skip the current iteration if KeyError occurs
    #cpu_requests 
        print("here we go")
        cpu_utilization = cpu_allocatable - cpu_request_sum  # Calculate remaining CPU
        memory_utilization = memory_allocatable - memory_request_sum  # Calculate remaining memory
    
        available_nodes.append({'name': node.metadata.name, 'cpu_allocatable': cpu_allocatable,
                                'memory_allocatable': memory_allocatable, 'cpu_usage': cpu_request_sum,
                                'memory_usage': memory_request_sum, 'cpu_remaining': cpu_utilization,
                                'memory_remaining': memory_utilization})

    return available_nodes


if __name__ == '__main__':
    # Create a Kubernetes client
    client = kubernetes.client.CoreV1Api()

    # Get a list of all the nodes in the cluster and their available resources
    available_nodes = nodes_available(client)

    # Print the list of available nodes
    print(available_nodes)



def main():
    a = nodes_available()
    print("---------------------------------")
    print(a)
