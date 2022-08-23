FROM centos:8
RUN cd /etc/yum.repos.d/
RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*

# RUN yum -y update
RUN dnf -y install -y git curl wget sudo

SHELL ["/bin/bash", "--login", "-c"]
# CMD /bin/bash

WORKDIR /CEASIOMpy/
RUN git clone https://github.com/cfsengineering/CEASIOMpy.git

# TO REMOVE
RUN cd CEASIOMpy && git checkout centos_install_script && cd ..

RUN chmod +x CEASIOMpy/installation/CentOS/install_*
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh
# RUN CEASIOMpy/installation/CentOS/install_miniconda.sh

RUN conda activate ceasiompy && CEASIOMpy/installation/CentOS/install_ceasiompy.sh


# WORKDIR /CEASIOMpy
# COPY . ../CEASIOMpy
# RUN git clone https://github.com/cfsengineering/CEASIOMpy.git
# # RUN echo "yes" | CEASIOMpy/installation/Ubuntu/install_miniconda.sh
# RUN ["/bin/bash","-c","source ~/.bashrc"]
# RUN CEASIOMpy/installation/Ubuntu/install_ceasiompy.sh
# RUN CEASIOMpy/installation/Ubuntu/install_pytornado.sh
# RUN CEASIOMpy/installation/Ubuntu/install_sumo.sh
# RUN CEASIOMpy/installation/Ubuntu/install_su2.sh
