#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2019
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA

FROM nvidia/cuda:10.1-devel as buildenv

RUN apt-get update
RUN apt-get install -y \
    git \
    python \
    python-pip \
    libpython-dev

RUN pip install virtualenv
RUN virtualenv /usr/local
RUN rm -rf /usr/local/local

WORKDIR /home
RUN git clone -b shao-demo https://github.com/ICRAR/jacal.git

WORKDIR /home/jacal/summit_demo
RUN ./compile_summit_software.sh -s ubuntu -j 6

##############################################################
# Create a new image based on only the executable parts of the old image
FROM nvidia/cuda:10.1-runtime

RUN apt-get update && \
    apt-get install -y \
    python \
    libgomp1 \
    libboost-dev \
    libboost-filesystem-dev\
    libboost-program-options-dev \
    libboost-signals-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libcfitsio-dev \
    libffi-dev \
    libfftw3-dev \
    libgsl-dev \
    liblog4cxx-dev \
    libopenblas-dev \
    libopenmpi-dev  \
    wcslib-dev \
    openssh-client

#############################################################
## This looks odd, but as the CUDA is in /usr/local I don't want to
## copy the big heavy devel CUDA into the runtime
WORKDIR /usr/local/bin
COPY --from=buildenv /usr/local/bin .
WORKDIR /usr/local/include
COPY --from=buildenv /usr/local/include .
WORKDIR /usr/local/lib
COPY --from=buildenv /usr/local/lib .

RUN ldconfig
