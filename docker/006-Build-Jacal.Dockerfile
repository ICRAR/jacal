#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2018
#    Copyright by UWA (in the framework of the ICRAR)
#
#    (c) Copyright 2018 CSIRO
#    Australia Telescope National Facility (ATNF)
#    Commonwealth Scientific and Industrial Research Organisation (CSIRO)
#    PO Box 76, Epping NSW 1710, Australia
#    atnf-enquiries@csiro.au
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
#

FROM jacal-005-git-jacal as buildenv

ARG PREFIX=/usr/local

RUN apt-get update && \
    apt-get install -y \
    g++ \
    make

RUN apt-get install -y \
    libboost-dev \
    libboost-filesystem-dev \
    libboost-program-options-dev \
    libboost-python-dev \
    libboost-regex-dev \
    libboost-signals-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libcfitsio-dev \
    liblog4cxx-dev \
    wcslib-dev

#############################################################
## Copy the YandaSoft libraries we need
COPY --from=jacal-003-build-yandasoft $PREFIX $PREFIX

#############################################################
## Copy the Daliuge libraries we need
COPY --from=jacal-004-daliuge $PREFIX $PREFIX
ENV PATH=$PREFIX/bin:$PATH
RUN ldconfig

#############################################################
## Move to the correct location
WORKDIR /home/jacal/apps/askap
RUN sed -i 's/namespace casa/namespace casacore/'  $PREFIX/include/askap/askap/CasacoreFwdDefines.h
COPY 006/Makefile.docker Makefile.docker
RUN make -f Makefile.docker
RUN cp libaskapsoft_dlg.so $PREFIX/lib

FROM debian:stretch-slim
# In multistage builds arguments don't copy over
ARG PREFIX=/usr/local

RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    libboost-dev \
    libboost-filesystem-dev \
    libboost-program-options-dev \
    libboost-python-dev \
    libboost-regex-dev \
    libboost-signals-dev \
    libboost-system-dev \
    libboost-thread-dev \
    libc6 \
    libcfitsio-dev \
    libcppunit-dev \
    libexpat1 \
    libffi-dev \
    libfftw3-dev \
    libgsl-dev \
    liblog4cxx-dev \
    libopenblas-dev \
    libopenmpi-dev \
    libssl1.1 \
    libxerces-c-dev \
    netbase \
    wcslib-dev

ENV PATH=${PREFIX}/bin:$PATH

#############################################################
## Copy jacal
COPY --from=buildenv ${PREFIX} ${PREFIX}

#############################################################
## Copy the YandaSoft libraries we need
COPY --from=jacal-003-build-yandasoft $PREFIX $PREFIX

#############################################################
## Copy the Daliuge libraries we need
COPY --from=jacal-004-daliuge $PREFIX $PREFIX
ENV PATH=$PREFIX/bin:$PATH

RUN ldconfig
