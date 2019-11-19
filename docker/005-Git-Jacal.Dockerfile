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

RUN apt-get update
RUN apt-get install -y \
    git

#############################################################
# The Jacal repo has a number of measurement sets in it that we don't need.
# All we need is the Apps
WORKDIR /home/jacal
RUN git init
RUN git remote add origin https://github.com/ICRAR/jacal.git
RUN git config core.sparseCheckout true
RUN echo "apps/" >> .git/info/sparse-checkout
RUN echo "shao_demo/" >> .git/info/sparse-checkout
RUN echo '!*.ms' >> .git/info/sparse-checkout
RUN echo '!functests' >> .git/info/sparse-checkout
RUN git pull origin master
