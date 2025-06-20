FROM centos:8

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
RUN dnf -y install -y git curl wget sudo unzip gcc-c++ tbb libXrender libXcursor libXinerama libXft
RUN dnf -y install mesa-libGLU mesa-libGL libSM

ENV CONDA_DIR=/opt/conda
RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

RUN conda init bash
RUN source ~/.bashrc
RUN conda update -n base -c defaults conda

# Copy
WORKDIR /CEASIOMpy/installation/CentOS/
COPY ./installation/CentOS/install_ceasiompy.sh .
COPY ./installation/CentOS/install_pyavl.sh .
COPY ./installation/CentOS/install_su2_without_mpi.sh .
RUN chmod +x install_*.sh

WORKDIR /CEASIOMpy/src/ceasiompy/utils
COPY ./src/ceasiompy/utils/moduleinterfaces.py .

# Install
WORKDIR /CEASIOMpy
COPY ./environment.yml .
RUN installation/CentOS/install_ceasiompy.sh && \
    installation/CentOS/install_pyavl.sh && \
    installation/CentOS/install_su2_without_mpi.sh
RUN source ~/.bashrc

WORKDIR /CEASIOMpy/CEASIOMpy/tests
# RUN conda activate ceasiompy && ./run_ci.sh
RUN bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate ceasiompy && ./run_ci.sh"
