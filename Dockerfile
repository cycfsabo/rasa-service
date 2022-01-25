FROM ubuntu:18.04
ENV LANG=en_US.utf8
ENV LANG C.UTF-8
RUN apt-get update && apt-get install -y apt-transport-https ca-certificates curl
RUN curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list
RUN apt-get update && apt-get install -y kubectl
RUN mkdir /root/.kube/
COPY config /root/.kube/
RUN export KUBECONFIG=/root/.kube/config

RUN curl https://get.helm.sh/helm-v3.8.0-rc.2-linux-amd64.tar.gz -o helm-v3.8.0-rc.2-linux-amd64.tar.gz
RUN tar -zxvf helm-v3.8.0-rc.2-linux-amd64.tar.gz
RUN mv ./linux-amd64/helm /usr/local/bin/helm
RUN apt-get install python3-pip -y 
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir -p /rasa-service
COPY . /rasa-service/
CMD ["sh", "-c", "cd /rasa-service/flask/ && export FLASK_APP=main.py && flask run --host=0.0.0.0"]
