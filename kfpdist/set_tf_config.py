from kubernetes import client, config
import json
import os
import time
import socket

def _check_rank0(ip, port):
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, port))
        if result == 0:
            break
        else:
            print("waiting rank0 %s:%d to become ready..." % (ip, port))
            time.sleep(2)
        sock.close()

def set_dist_train_config(rank, nranks, step_name, port=9888):
    wf_id = os.getenv('WORKFLOW_ID')
    ns = os.getenv('KFP_NAMESPACE')
    if not wf_id or not ns:
        raise ValueError('WORKFLOW_ID and KFP_NAMESPACE env must be set in the workflow pod!')

    config.load_incluster_config()
    api = client.CustomObjectsApi()
    
    worker_started = 0
    while worker_started != nranks:
        resource = api.get_namespaced_custom_object(
            group="argoproj.io",
            version="v1alpha1",
            name=wf_id,
            namespace=ns,
            plural="workflows",
        )
        nodes = resource["status"]["nodes"]
        workers_spec = []
        for nk in nodes:
            node_info = nodes[nk]
            if node_info['templateName'] == step_name and node_info['type'] == 'Pod':
                podid = node_info['id']
                for input_param in node_info['inputs']['parameters']:
                    if input_param['name'].endswith('loop-item'):
                        # FIXME: argo parameter with "loop-item" is the rank.
                        curr_rank = int(input_param['value'])
                        break
                v1 = client.CoreV1Api()
                podinfo = v1.read_namespaced_pod(podid, ns)
                workers_spec.append((curr_rank, '%s:%d' % (podinfo.status.pod_ip, port)))
        worker_started = len(workers_spec)
        time.sleep(2)

    workers_spec.sort(key=lambda item: item[0])
    workers_spec_list = [i[1] for i in workers_spec]
    # set TF_CONFIG env for tf dist train
    os.environ['TF_CONFIG'] = json.dumps({
        'cluster': {
            'worker': workers_spec_list
        },
        'task': {'type': 'worker', 'index': rank}
    })
    print("Setting TF_CONFIG: %s" % os.environ['TF_CONFIG'])

    if rank != 0:
        # wait for rank0 to become ready.
        addr = workers_spec_list[0].split(':')
        ip = addr[0]
        port = int(addr[1])
        _check_rank0(ip, port)
