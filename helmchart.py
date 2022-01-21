import subprocess
import yaml
import json

def run_command(bashCommand, servicename="", file_path="", namespace="",):
    bashCommand = bashCommand + " " + servicename + " " +file_path + " -n " + namespace
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

def read_yaml_file(file_path):
    with open(file_path) as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        return data


def write_yaml_file(file_path, dictionary):
    datas = yaml.safe_load(json.dumps(dictionary))
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(datas, file, default_flow_style=False, allow_unicode=True)


class HelmChart:
    def __init__(self, service_name, image_name, image_tag, port, node_affinities: list, model_endpoint):
        self.service_name = service_name
        self.image_name = image_name
        self.image_tag = image_tag
        self.port = port
        self.node_affinities = node_affinities
        self.model_endpoint = model_endpoint

    def chart_generator(self, namespace):
        run_command("helm install", self.service_name)
    
    def create_configmaps(self):
        file_path = "./" + self.service_name + "/templates/configmaps.yaml"
        configmaps_data = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {
            'name': self.service_name+'-configmaps'}, 'data': {'MODEL_ENDPOINT': self.model_endpoint, 'BOT_NAME': self.service_name}}
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
            {'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': self.node_affinities}]}]}}}
        write_yaml_file(file_path, values_data)
    
    def customize_deployment(self):
        file_path = "./" + self.service_name + "/templates/deployment.yaml" + 
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
                                                    {"configMapRef": {"name": self.service_name "-configmaps"}}
                                                ],
                                                "image": self.image_name + ":" + self.image_tag,
                                                "name": self.service_name + "-container",
                                                "ports": [{"containerPort": self.port, "name": "http"}],
                                            }
                                        ],
                                        "serviceAccountName": self.service_name,
                                    },
                                },
                            },
                        }
        write_yaml_file(file_path, deployment_data)

        