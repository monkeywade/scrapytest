#! /usr/bin/env python3

import requests


class NodeResource:
    def __init__(self, nodename, podname, request_mem):
        self.nodename = nodename
        self.podname = podname
        self.request_mem = request_mem


resource_url = "https://10.96.0.1:443/api/v1/pods?fieldSelector=spec.nodeName%3d"
headers = {
    "Accept": "application/json, text/plain, */*",
    "Authorization": "Bearer ",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36",
}

node_resources = []
for node in ["node1", "node2", "node3", "node5", "node6", "node7"]:
    node_resource_url = resource_url + node
    node_resource_resp = requests.get(node_resource_url, headers=headers, verify=False)
    items = node_resource_resp.json().get("items")
    for item in items:
        pod_name = item["metadata"]["name"]
        containers = item["spec"]["containers"]
        pod_mem_resource_list = []
        # 统计pod的resource.memory值
        score = 0
        for container in containers:
            resources = container["resources"].get("requests")
            if not resources or not resources.get("memory"):
                pod_mem_resource_list.append(0)
            else:
                request_mem = int(resources.get("memory").rstrip("MiG"))
                if request_mem == 1:
                    request_mem = 1024
                score += request_mem
                pod_mem_resource_list.append(score)
        if sum(pod_mem_resource_list) == 0:
            score = 200
        node_resources.append(NodeResource(node, pod_name, score))
node_score = {}
for node_resource in node_resources:
    nodename = node_resource.nodename
    request_mem = node_resource.request_mem
    if nodename in node_score:
        node_score[nodename] += int(request_mem + request_mem / 16 / 1024)
    else:
        node_score[nodename] = int(request_mem + request_mem / 16 / 1024)

alloc_mem = 16 * 1024
for node in node_score:
    node_request_mem = node_score[node]
    node_resource_score = (alloc_mem - node_request_mem - 512) * 100 / alloc_mem / 2 + (
                100 - node_request_mem / alloc_mem * 100)
    print(node, ("%.2f" % node_resource_score))
