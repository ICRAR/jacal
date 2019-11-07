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

##############################################################
##
## | \ | |/ _ \_   _| ____|
## |  \| | | | || | |  _|
## | |\  | |_| || | | |___
## |_| \_|\___/ |_| |_____|
##
## The two dockerfiles need to be kept in sync
##
##############################################################

FROM python:3.7-slim-stretch as buildenv

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libc6-dev \
        libffi-dev \
        libssl-dev \
        make \
        g++ \
        git

RUN pip3 install --upgrade pip
RUN pip3 install git+https://github.com/ICRAR/daliuge.git

##############################################################
# Create a new image based on only the executable parts of the old image
FROM debian:stretch-slim

# In multistage builds arguments don't copy over
ARG PREFIX=/usr/local

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        libc6 \
        libffi6 \
        libssl1.1 \
        ca-certificates \
        netbase \
        libexpat1

COPY --from=buildenv ${PREFIX} ${PREFIX}
ENV PATH=${PREFIX}/bin:$PATH
