import shutil
import subprocess
import yaml
import json

def run_command(bashCommand, service_name="", namespace="",):
    if bashCommand == "helm create":
        bashCommand = bashCommand + " " + service_name
    elif bashCommand == "helm install" or bashCommand == "helm upgrade":
        file_path = "./" + service_name + "/"
        bashCommand = bashCommand + " " + service_name + " " +file_path + " -n " + namespace
    elif bashCommand == "helm uninstall":
        bashCommand = bashCommand + " " + service_name + " -n " + namespace
    elif bashCommand == "helm list":
        bashCommand = bashCommand + " -n " + namespace
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output = subprocess.check_output(('awk','NR>1 {print $1}'),stdin=process.stdout)
    return output

def read_yaml_file(file_path):
    with open(file_path) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        return data


def write_yaml_file(file_path, dictionary):
    datas = yaml.safe_load(json.dumps(dictionary))
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(datas, file, default_flow_style=False, allow_unicode=True)


class HelmChart:
    def __init__(self, service_name, image_name, image_tag, port, node_affinity: list, model_endpoint, namespace):
        self.service_name = service_name
        self.image_name = image_name
        self.image_tag = image_tag
        self.port = port
        self.node_affinity = node_affinity
        self.model_endpoint = model_endpoint
        self.namespace = namespace

    def helm_create(self):
        run_command(bashCommand = "helm create", service_name = self.service_name)
    
    def chart_delete(self):
        file_path = "./" + self.service_name + "/"
        shutil.rmtree(file_path)
    
    def helm_install(self):
        run_command(bashCommand = "helm install", service_name = self.service_name, namespace = self.namespace)

    def helm_uninstall(self):
        run_command(bashCommand= "helm uninstall", service_name= self.service_name, namespace= self.namespace)

    def create_configmaps(self):
        file_path = "./" + self.service_name + "/templates/configmaps.yaml"
        configmaps_data = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {
            'name': self.service_name+'-configmaps'}, 'data': {'MODEL_ENDPOINT': self.model_endpoint, 'BOT_NAME': self.service_name, 'NODE_PORT': '5006', 'REDIS_CHAT_HOST': 'rasa-instances-redis', 'REDIS_HOST': 'rasa-instances-redis', 'REDIS_NODE_DB': '3'}}
        write_yaml_file(file_path, configmaps_data)

    def customize_values(self):
        file_path = "./" + self.service_name + "/values.yaml"
        values_data = read_yaml_file(file_path)
        image = values_data["image"]
        image["repository"] = self.image_name
        image["tag"] = self.image_tag
        values_data["imagePullSecrets"] = [{'name': 'habour-registry'}]
        values_data["service"]["port"] = self.port
        values_data["affinity"] = {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [
            {'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': self.node_affinity}]}]}}}
        write_yaml_file(file_path, values_data)
    
    def customize_deployment(self):
        file_path = "./" + self.service_name + "/templates/deployment.yaml" 
        labels = {
                'app.kubernetes.io/instance': self.service_name,
                'app.kubernetes.io/managed-by': 'Helm',
                'app.kubernetes.io/name': self.service_name,
                'app.kubernetes.io/version': '1.16.0',
                'helm.sh/chart': self.service_name+'-0.1.0'
            }

        deployment_data = {
                            "apiVersion": "apps/v1",
                            "kind": "Deployment",
                            "metadata": {
                                "name": self.service_name,
                                "labels": labels,
                            },
                            "spec": {
                                "replicas": 1,
                                "selector": {"matchLabels": labels},
                                "template": {
                                    "metadata": {"labels": labels},
                                    "spec": {
                                        "containers": [
                                            {
                                                "envFrom": [
                                                    {"configMapRef": {"name": self.service_name + "-configmaps"}}
                                                ],
                                                "command": ["./run_node.sh"],
                                                "image": self.image_name + ":" + self.image_tag,
                                                "name": self.service_name + "-container",
                                                "ports": [{"containerPort": self.port, "name": "port05"},{"containerPort": 5006, "name": "port06"}],
                                            }
                                        ],
                                        "serviceAccountName": self.service_name,
                                        "affinity": {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': self.node_affinity}]}]}}}
                                    },
                                },
                            },
                        }
        write_yaml_file(file_path, deployment_data)

        