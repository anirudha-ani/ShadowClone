# ShadowClone

---

This project is developed on PopOS 22.04 and with Docker Engine (Not docker desktop cause on Linux it runs on it's own virtual environemnt) and MiniKube. So behaviour might not be similar accross all the OSs.

## Disclaimer 
There is another issue posted on [aiortc github](https://github.com/aiortc/aiortc/issues/731) that OpenCV `imshow` does not work when the same file has `import aiortc` . It was similar in my case. That's why in my client I could not show the continuous video frame. But I have put a code segment to save each of the received frame. That's one way to know the server client connection is working.  

---
## Run the project
---
## Running Locally

1. From terminal go to `server` directory.
2. Run this command to install dependencies
```bash
$ pip install -r requirements.txt
``` 

3. Run the below command to run the server
```bash
$ python server.py
``` 
4. Then from terminal go to `client` directory.
5. Run this command to install dependencies
```bash
$ pip install -r requirements.txt
``` 

6. Run the below command to run the server
```bash
$ python client.py
``` 

---

## Running From docker
1. Install docker by following this [instruction](https://docs.docker.com/engine/install/ubuntu/) (Only for Ubuntu derrivatives) 
1. From terminal go to `server` directory. 
2. Run this command shell script. It will take care of all the configuration and launch the server in docker 
```bash
$ sh runServerDocker.sh
``` 

5. Run this command to launch the client in docker
```bash
$ sh runClientDocker.sh
``` 

---

## Running Through Kubernetes

1. Install MiniKube+Kubectl and start them locally by following the instructions [here](https://minikube.sigs.k8s.io/docs/start/)
2. Open terminal and make docker environment to point to Kubernetes docker repo by running the following command
```bash
   eval $(minikube -p minikube docker-env)
```
3. Now go to `server` directory using cd command to build the docker image using the command
```bash
docker build -t server-image .
```
4. Now go to `client` directory using cd command to build the docker image using the command
```bash
docker build -t client-image .
```
5. Now the kubernetes can find the corrosponding images, though it does not exist in the actual docker hub
6. From `server` directory run the command to trigger the Kubernetes configuration described in `server.yaml`. It will run `server-image` docker as development pods.
```bash
kubectl apply -f "server.yaml" 
```
7. From `client` directory run the command to trigger the Kubernetes configuration described in `client.yaml`. It will run `client-image` docker as development pods.
```bash
kubectl apply -f "client.yaml" 
```
8. You can stop and delete the pods using the following command
```bash
kubectl delete -f "*FILENAME*.yaml" 
```

## Testing
The functions are not independent enough to be unit testable
