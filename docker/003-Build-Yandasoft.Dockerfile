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


FROM jacal-002-libraries as buildenv

ARG PREFIX=/usr/local
ARG JOBS=6

WORKDIR /home/yandasoft
RUN ./build_all.sh -s ubuntu -p ${PREFIX} -S -c -a -r -y -j ${JOBS}

WORKDIR /

##############################################################
# Create a new image based on only the executable parts of the old image
FROM debian:stretch-slim
# In multistage builds arguments don't copy over
ARG PREFIX=/usr/local
COPY --from=buildenv ${PREFIX} ${PREFIX}
COPY --from=buildenv /home/yandasoft/askap/askap_synthesis.h ${PREFIX}/include/askap
