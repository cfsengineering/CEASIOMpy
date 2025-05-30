# INSTALLATION with Docker

## Install Docker

For installation instructions, visit [Docker's official website](https://docs.docker.com/get-started/get-docker/).

## Install CEASIOMpy

Permissions:

Run the following command.

```bash
docker ps -a
```

If you do not have the necessary permissions to run Docker, add your user to the Docker group. Otherwise, you can skip this step.

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Clone the CEASIOMpy repository in a folder of your choice:

```bash
cd path/to/the/folder/
git clone https://github.com/cfsengineering/CEASIOMpy
cd CEASIOMpy
```

Build the Docker image for your system's architecture:

# Determine your computer's architecture:

- Linux/macOS: Run uname -m in the terminal. Look for x86_64/amd64 (Intel/AMD) or arm64/aarch64 (ARM).
- Windows: Run echo %PROCESSOR_ARCHITECTURE% in Command Prompt/PowerShell. Look for AMD64 (Intel/AMD) or ARM64 (ARM).

# Run the appropriate build command:
```bash
docker build --platform=linux/amd64 -t ceasiompy-image -f CEASIOMpy_docker_Installation .
```

Run the Docker container (you need to modify /pathtoYOURlocal/CEASIOMpy with the absolute path of your CEASIOMpy's folder location):

On Linux/macOS:

```bash
docker run --init -it --rm --net=host \
-e DISPLAY=$DISPLAY \
-e LIBGL_ALWAYS_SOFTWARE=1 \
-e OMPI_ALLOW_RUN_AS_ROOT=1 \
-e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-p 8501:8501 \
-v /pathto/CEASIOMpy:/CEASIOMpy \
ceasiompy-image
```

On Windows:

```bash
docker run -it --rm -e DISPLAY=$DISPLAY -e LIBGL_ALWAYS_SOFTWARE=1 -e OMPI_ALLOW_RUN_AS_ROOT=1 -e OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1 -v /tmp/.X11-unix:/tmp/.X11-unix -p 8501:8501 -v C:/username/pathto/CEASIOMpy:/CEASIOMpy ceasiompy-image
```

You can now click on local URL and use CEASIOMpy's GUI (Graphical User Interface) with all of its required software.
