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

FROM debian:stretch-slim

ARG PREFIX=/usr/local

RUN apt-get update
RUN apt-get install -y \
    git \
    wget

#############################################################
# Get YandaSoft, the build will load the other dependencies
#
WORKDIR /home
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/yandasoft.git
WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/lofar-common.git
WORKDIR /home/yandasoft/lofar-common
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/lofar-blob.git
WORKDIR /home/yandasoft/lofar-blob
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-askap.git
WORKDIR /home/yandasoft/base-askap
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-logfilters.git
WORKDIR /home/yandasoft/base-logfilters
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-imagemath.git
WORKDIR /home/yandasoft/base-imagemath
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-askapparallel.git
WORKDIR /home/yandasoft/base-askapparallel
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-scimath.git
WORKDIR /home/yandasoftbase-scimath
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-accessors.git
WORKDIR /home/yandasoft/base-accessors
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/base-components.git
WORKDIR /home/yandasoft/base-components
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-pipelinetasks.git
WORKDIR /home/yandasoft/askap-pipelinetasks
RUN git clone https://bitbucket.csiro.au/scm/askapsdp/askap-cmake

WORKDIR /home/yandasoft
RUN git clone https://github.com/casacore/casacore

WORKDIR /home/yandasoft
RUN git clone https://github.com/steve-ord/casarest -b components-only

#############################################################
## Get the Common CasaCore data
WORKDIR $PREFIX/share/casacore/data
RUN wget ftp://ftp.astron.nl/outgoing/Measures/WSRT_Measures.ztar
RUN tar -xvf WSRT_Measures.ztar
RUN rm WSRT_Measures.ztar

WORKDIR /home/yandasoft