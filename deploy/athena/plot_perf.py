#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2017
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

import numpy as np
import matplotlib.pyplot as plt

def read_csv(fname, delimiter=',', mode=1):
    """
    mode: 1 - anything but the first column
    mode: 0 - just the first column
    """
    mode = min(1, mode)
    with open(fname, 'r') as fin:
        for line in fin:
            try:
                yield line.strip().split(delimiter, 1)[mode]
            except IndexError:
                continue

def plot_time_vs_cn(csv_file='/Users/Chen/proj/jacal_icrar/deploy/athena/result',
                    second_csv='/Users/Chen/proj/jacal_icrar/deploy/athena/result_ib'):
    """
    X axis - Channel_Node combination
    Y1 axis - time
    Y2 axis - number of Drops
    """
    x_axis_labels = [x for x in read_csv(csv_file, mode=0)]
    num_drops = [int(x.split('C')[0]) * 4 for x in x_axis_labels]
    data = np.loadtxt(read_csv(csv_file), delimiter=',')
    if (second_csv is not None):
        data1 = np.loadtxt(read_csv(second_csv), delimiter=',')
        data1[0:2, :] = None
    X = np.arange(data.shape[0])

    fig, ax1 = plt.subplots()
    ax1.plot(X, data[:, 0], label='Drop creation time (Ethernet)', marker='o',
             markersize=8, markeredgecolor='b', markerfacecolor="None",
             markeredgewidth=2, linewidth=2)
    ax1.plot(X, data[:, 1], label='Graph execution time (Ethernet)', marker='x',
             markersize=8, markeredgewidth=2, linewidth=2)
    if (second_csv is not None):
        ax1.plot(X, data1[:, 0], label='Drop creation time (IB)', marker='*',
                 markersize=14, markeredgecolor='b', markerfacecolor="None",
                 markeredgewidth=2, linewidth=2, color='blue')
        ax1.plot(X, data1[:, 1], label='Graph execution time (IB)', marker='D',
                 markersize=8, markeredgewidth=2, linewidth=2, color='green',
                 markerfacecolor="None", markeredgecolor='g')
    ax2 = ax1.twinx()
    ax2.plot(X, num_drops, label='Number of Drops', color='r', marker='^',
             markersize=8, markeredgecolor='r', markerfacecolor="None",
             markeredgewidth=2, linewidth=2)
    ax1.set_ylim([0, 100])
    ax1.set_yticks(np.arange(0, 100+1, 10))
    ax1.set_ylabel('Time in seconds', fontsize=16)
    ax1.set_xlabel('Channel and Node combination', fontsize=16)

    ax2.set_ylabel('Number of Drops', fontsize=16)
    ax1.set_xlim([-1, len(X)])
    plt.xticks(X, x_axis_labels)
    ax1.tick_params('x', labelsize=14)
    ax1.legend(loc='center left')
    ax2.legend(loc='upper right')
    ax1.grid(True, linestyle='-', which='major', color='lightgrey',
               alpha=1.0, axis='y')
    for tick in ax1.get_xticklabels():
        tick.set_rotation(20)
    plt.suptitle('Time measurement of a Jacal test pipeline on Athena', fontsize=17)
    #plt.tight_layout()
    plt.show()

if __name__=='__main__':
    plot_time_vs_cn()
