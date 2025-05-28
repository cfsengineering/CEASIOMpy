FROM centos:8

RUN sed -i 's/mirrorlist/#mirrorlist/g' /etc/yum.repos.d/CentOS-*
RUN sed -i 's|#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|g' /etc/yum.repos.d/CentOS-*
RUN dnf -y install -y git curl wget sudo unzip gcc-c++ tbb libXrender libXcursor libXinerama libXft

ENV CONDA_DIR /opt/conda
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
COPY ./installation/CentOS/install_su2.sh .
RUN chmod +x install_*.sh

# Install
WORKDIR /CEASIOMpy
COPY ./environment.yml .
RUN installation/CentOS/install_ceasiompy.sh \
    installation/CentOS/install_pyavl.sh && \
    installation/CentOS/install_su2.sh
RUN source ~/.bashrc

# Copy test script
WORKDIR /CEASIOMpy/tests
COPY ./tests/run_ci.sh .
RUN chmod +x run_ci.sh

# Run
WORKDIR /CEASIOMpy
RUN conda run -n ceasiompy tests/run_ci.sh
