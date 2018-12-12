#
# ICRAR - International Centre for Radio Astronomy Research
# (c) UWA - The University of Western Australia, 2018
# Copyright by UWA (in the framework of the ICRAR)
#
# (c) Copyright 2018 CSIRO
# Australia Telescope National Facility (ATNF)
# Commonwealth Scientific and Industrial Research Organisation (CSIRO)
# PO Box 76, Epping NSW 1710, Australia
# atnf-enquiries@csiro.au
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307  USA
#
import argparse

from casacore import tables

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output', help='The table to write', default='my_table')
    parser.add_argument('-t', '--column-type', help='The type of the column to write', default='float')
    parser.add_argument('-c', '--column-name', help='The name of the column to write', default=None)
    parser.add_argument('-e', '--even', action='store_true', help='Write only from even ranks (to check sub-communicator writing)', default=False)
    parser.add_argument('-n', '--nrows', type=int, help='Number of rows to write per rank', default=100)
    parser.add_argument('-A', '--no-adios', action='store_true', help='Do not use ADIOS2', default=False)

    opts = parser.parse_args()

    colname = opts.column_name or 'MY_%s_COLUMN' % opts.column_type.upper()
    ref_val = None
    if opts.column_type == 'float':
        ref_val = 0.
    elif opts.column_type == 'int':
        ref_val = 0
    elif opts.column_type == 'bool':
        ref_val = False
    else:
        parser.error('Only float, int and bool are supported column type names')

    from mpi4py import MPI
    comm = MPI.COMM_WORLD
    size = comm.Get_size()
    rank = comm.Get_rank()

    if opts.even:
        size = (size + 1) // 2

    kwargs = {'datamanagertype': 'Adios2StMan'} if not opts.no_adios else {}
    scd = tables.makescacoldesc(colname, ref_val, **kwargs)
    td = tables.maketabdesc([scd])
    t = tables.table(opts.output, td, nrow=opts.nrows * size)
    with t:
        if opts.even and rank % 2 != 0:
            return
        tc = tables.tablecolumn(t, colname)
        start = opts.nrows * rank
        if opts.even:
            start //= 2
        tc[start:start + opts.nrows] = range(opts.nrows)

if __name__ == '__main__':
    main()
