#!/bin/bash

# Stop and remove the existing container
docker stop server-container
docker rm server-container

# Remove the existing image
docker rmi server-image

# Build the new image
docker build -t server-image .

docker run -it --rm \
    --name server-container \
    -p 1234:1234 \
    server-image

# xhost + 
# Run a new container from the updated image

# docker run -it --rm \
#     --name server-container \
#     -e DISPLAY \
#     -e QT_X11_NO_MITSHM=1 \
#     -v /tmp/.X11-unix:/tmp/.X11-unix \
#     -v $HOME/.Xauthority:/root/.Xauthority \
#     server-image