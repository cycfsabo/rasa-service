import subprocess
from importlib_metadata import metadata
import yaml
import json

# class HelmChart:
#     def __init__(self, chart_name):
#         self.chart_name = chart_name

#     def chart_generator(self):


def create_helm_chart(name):
    bashCommand = "helm create " + name
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

def install_helm_chart(service_name, chart_path, namespace):
    bashCommand = "helm install " + service_name + " " + chart_path + " -n" + namespace
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()

def upgrade_helm_chart(service_name, chart_path, namespace):
    bashCommand = "helm upgrade " + service_name + " " + chart_path + " -n" + namespace
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()    

def unistall_helm_chart(service_name, chart_path, namespace):
    bashCommand = "helm uninstall " + service_name + " -n" + namespace
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


def read_text_file(file_path):
    with open(file_path) as file:
        data = file.read()
        return data


def create_configmaps(service_name, file_path, model_endpoint):
    configmaps_data = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {
        'name': service_name+'-configmaps'}, 'data': {'MODEL_ENDPOINT': model_endpoint, 'BOT_NAME': service_name}}
    write_yaml_file(file_path, configmaps_data)


# create_configmaps('rasa-bot-02', './test/templates/configmaps.yaml', 'https://ic-storage.vnpt.vn')


def customize_values(file_path, image_name, image_tag, port, node_affinities: list):
    values_data = read_yaml_file(file_path)
    image = values_data["image"]
    image["repository"] = image_name
    image["tag"] = image_tag
    values_data["imagePullSecrets"] = [{'name': 'habour-registry'}]
    values_data["service"]["port"] = port
    values_data["affinity"] = {'nodeAffinity': {'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [
        {'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'In', 'values': node_affinities}]}]}}}
    write_yaml_file(file_path, values_data)

# customize_values("./test/values.yaml", "redis", "latest", "5003", node_affinities=["node1", "node2"])


def customize_deployment(file_path, service_name, image_name, image_tag, port):
    labels = {
            'app.kubernetes.io/instance': service_name,
            'app.kubernetes.io/managed-by': 'Helm',
            'app.kubernetes.io/name': service_name,
            'app.kubernetes.io/version': '1.16.0',
            'helm.sh/chart': service_name+'-0.1.0'
        }

    deployment_data = {'apiVersion': 'apps/v1', 
                        'kind': 'Deployment',
                        'metadata': {
                            'name': service_name,
                            'labels': labels,
                        }, 'spec': {
                            'replicas': 1,
                            'selector': {
                                'matchLabels': labels
                                },
                                'template': {
                                    'metadata': {
                                        'labels': labels
                                    },
                                    'spec':{
                                        'containers': [{
                                                'envFrom':[{
                                                    'configMapRef': {
                                                        'name': service_name+'-configmaps'
                                                    }
                                                }],
                                                'image': image_name + ":" + image_tag,
                                                'name': service_name + '-container',
                                                'ports':[{
                                                    'containerPort': port,
                                                    'name': 'http'
                                                }]
                                    }],
                                        'serviceAccountName': service_name
                                    }
                                }
                        }
                        }
    write_yaml_file(file_path, deployment_data)


customize_deployment("./test/templates/deployment.yaml", 'test', 'nginx', 'latest', 5003)
create_configmaps('test', './test/templates/configmaps.yaml', 'https://ic-storage.vnpt.vn')


# with open("./test/templates/deployment.yaml") as f:
#     data = yaml.load(f, Loader=yaml.BaseLoader)
#     print(data)
