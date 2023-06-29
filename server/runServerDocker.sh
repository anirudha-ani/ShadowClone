#!/bin/bash

# Stop and remove the existing container
docker stop server-container
docker rm server-container
docker rm mynetwork
docker network create mynetwork

# Remove the existing image
docker rmi server-image

# Build the new image
docker build -t server-image .

docker run -it --rm \
    --name server-container \
    --network mynetwork \
    server-image
    
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