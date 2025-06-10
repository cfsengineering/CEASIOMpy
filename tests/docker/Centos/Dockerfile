FROM centos:8

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
RUN dnf -y install -y git curl wget sudo unzip gcc-c++ tbb libXrender libXcursor libXinerama libXft
RUN dnf -y install mesa-libGLU mesa-libGL libSM

SHELL ["/bin/bash", "--login", "-c"]

WORKDIR /CEASIOMpy/
RUN git clone https://github.com/cfsengineering/CEASIOMpy.git
RUN chmod +x CEASIOMpy/installation/CentOS/install_*
ENV CONDA_DIR /opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda init bash
RUN source ~/.bashrc
RUN conda update -n base -c defaults conda

WORKDIR /CEASIOMpy/CEASIOMpy/installation/CentOS/
RUN chmod +x install_*.sh
RUN ./install_ceasiompy.sh
RUN ./install_pyavl.sh
RUN ./install_su2.sh
RUN source ~/.bashrc

WORKDIR /CEASIOMpy/CEASIOMpy/tests
# RUN conda activate ceasiompy && ./run_ci.sh
RUN bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate ceasiompy && ./run_ci.sh"

