# from black import re
# from pyrsistent import PTypeError
from crypt import methods
from helmchart import *
from flask import *

# service = helmchart.HelmChart("rasa-01", "nginx", "latest", 80, node_affinities=["node1", "node2"], model_endpoint="https://ic-storage.vnpt.vn",namespace="test-avionix")

# service.helm_create()
# service.create_configmaps()
# service.customize_values()
# service.customize_deployment()
# service.helm_install()
# service.chart_delete()

# service.helm_uninstall()


from flask import Flask
from flask import request

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/create",methods=['POST'])
def create_service():
    data = request.json
    service_name = data["service_name"]
    image_name = data["image_name"]
    image_tag = data["image_tag"]
    port = data["port"]
    node_affinity = data["node_affinity"]
    model_endpoint = data["model_endpoint"]
    namespace = data["namespace"]
    try:
        service = HelmChart(service_name, image_name, image_tag, port, node_affinity, model_endpoint, namespace)
        service.helm_create()
        service.create_configmaps()
        service.customize_values()
        service.customize_deployment()
        service.helm_install()
        service.chart_delete()
        return "Success!"
    except:
        return "Error!"


@app.route("/delete",methods=['POST'])
def delete_service():
    data = request.json
    print(data)
    try:
        run_command(bashCommand= "helm uninstall", service_name= data['service_name'], namespace= data['namespace'])
        return "Success!"
    except:
        return "Error!"

@app.route("/list",methods=['GET'])
def list_service():
    namespace = request.args.get('ns')
    try:
        return run_command(bashCommand= "helm list", namespace= namespace)
    except:
        return "Error!"

if __name__ == "__main__":
    app.run(host='0.0.0.0')