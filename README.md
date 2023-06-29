# Nimble Robotics Takehome Assesment

Subimission by Anirudha Paul

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

## Testing
The functions are not indipendent enough to be unit testable
