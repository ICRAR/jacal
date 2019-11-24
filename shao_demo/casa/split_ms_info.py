
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2019
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
from os.path import join

out_path = 'dummy'
channel1_freq = 1151500000.0
channel_width = 18518.518518518198
bottom_channel = 7746
top_channel = 15552
nodes = 6
cores = 24
step_size = (top_channel - bottom_channel) / (nodes * cores)
step_size = int(step_size)
loop_count = 1

for i in range(bottom_channel, top_channel, step_size):
    upper = i + step_size -1
    spw_text = f'0:{i}~{upper}'
    low = i * channel_width
    low += channel1_freq
    low /= 1e6
    low = round(low, 1)
    high = upper * channel_width
    high += channel1_freq
    high /= 1e6
    high = round(high, 1)
    output_vis = join(f'{out_path}', f'file_{low}_{high}.ms')
    print(f'{loop_count}: ["file_{low}_{high}.ms", {i}, {upper}],')
    loop_count += 1
