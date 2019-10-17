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
    git

WORKDIR /home
RUN git clone https://github.com/ICRAR/jacal.git

WORKDIR /home/jacal/summit_demo
RUN ./compile_summit_software.sh -s ubuntu -j 6

##############################################################
# Create a new image based on only the executable parts of the old image
FROM nvidia/cuda:10.1-runtime
COPY --from=buildenv /usr/local /usr/local
RUN ldconfig
