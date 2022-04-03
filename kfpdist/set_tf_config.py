from kubernetes import client, config
import json
import os
import time

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
                v1 = client.CoreV1Api()
                podinfo = v1.read_namespaced_pod(podid, ns)
                workers_spec.append('%s:%d' % (podinfo.status.pod_ip, port))
        worker_started = len(workers_spec)
        time.sleep(2)

    # set TF_CONFIG env for tf dist train
    os.environ['TF_CONFIG'] = json.dumps({
        'cluster': {
            'worker': workers_spec
        },
        'task': {'type': 'worker', 'index': rank}
    })

