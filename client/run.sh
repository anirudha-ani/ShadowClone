#!/bin/bash

# Stop and remove the existing container
docker stop client-container
docker rm client-container

# Remove the existing image
docker rmi client-image

# Build the new image
docker build -t client-image .
SERVERIP=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' server-container`
docker run -it --rm \
    --name client-container \
    -e SERVERIP=$SERVERIP \
    --network mynetwork \
    client-image

# this configuration is for graphical display usage
# xhost + 
# Run a new container from the updated image

# docker run -it --rm \
#     --name server-container \
#     -e DISPLAY \
#     -e QT_X11_NO_MITSHM=1 \
#     -v /tmp/.X11-unix:/tmp/.X11-unix \
#     -v $HOME/.Xauthority:/root/.Xauthority \
#     server-image