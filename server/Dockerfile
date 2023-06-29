# Base image
FROM python:3.10

RUN apt-get update && apt-get install -y --no-install-recommends \
      bzip2 \
      g++ \
      git \
      graphviz \
      libgl1-mesa-glx \
      libhdf5-dev \
      openmpi-bin \
      wget \
      python3-tk && \
    rm -rf /var/lib/apt/lists/*
    
# Setting up working directory 
RUN mkdir /src
WORKDIR /src

# Copy the Python file from the local directory to the container
COPY . .

# Install any necessary dependencies
# If you have a requirements.txt file, uncomment the following line
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the entrypoint to run the Python file
CMD ["python", "BallGeneration.py"]