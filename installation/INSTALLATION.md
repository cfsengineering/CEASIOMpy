# CEASIOMpy installation

## :warning: **Warning**

*Unless required by applicable law or agreed to in writing, Licensor provides the Work (and each Contributor provides its Contributions) on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied, including, without limitation, any warranties or conditions of TITLE, NON-INFRINGEMENT, MERCHANTABILITY, or FITNESS FOR A PARTICULAR PURPOSE. You are solely responsible for determining the appropriateness of using or redistributing the Work and assume any risks associated with Your exercise of permissions under the [License](https://github.com/cfsengineering/CEASIOMpy/blob/main/LICENSE).*


## INSTALLATION with Docker (Recommended)

# Install Docker

For installation instructions, visit [Docker's official website](https://docs.docker.com/get-started/get-docker/).

# Install CEASIOMpy

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

Now build the Docker image by using the command:

```bash
docker build --platform=linux/amd64 -t ceasiompy:local -f CEASIOMpy_docker_Installation .
```

Run the Docker container (you need to modify /pathtoYOURlocal/CEASIOMpy with the absolute path of your CEASIOMpy's folder location):

```bash
docker run -it --rm \
-e DISPLAY=$DISPLAY \
-e LIBGL_ALWAYS_SOFTWARE=1 \
-v /tmp/.X11-unix:/tmp/.X11-unix \
-v /pathtoYOURlocal/CEASIOMpy:/CEASIOMpy \
ceasiompy-image
```

You can now click on External URL and use CEASIOMpy's GUI (Graphical User Interface) with all of its required software.


## NATIVE INSTALLATION (not recommended)

Click on the link to install CEASIOMpy on:
    - [Linux](LINUX_INSTALLATION.md)
    - [MacOS](MAC_OS_INSTALLATION.md)
    - [Windows](Windows_INSTALLATION.md)