import sys

from matplotlib import pyplot as plt
import numpy as np

def heatmap(fname):
    data = np.loadtxt(fname, dtype={'names': ('node', 'time', 'evt'),
                                    'formats': ('i4', 'f4', 'S11')})
    unique_nodes = set(data['node'])
    node_range = min(unique_nodes), max(unique_nodes) + 1
    n_nodes = node_range[1] - node_range[0]

    fig = plt.figure(figsize=(100, 36))
    ax = fig.add_subplot(1, 1, 1)
    H, xedges, yedges = np.histogram2d(data['node'], data['time'], bins=(n_nodes, 1000))
    ax.imshow(H, cmap='hot')
    fig.savefig('heatmap.pdf')

    for evt in ('send_vis', 'ms_write', 'relay_heap'):
        selection = np.where(data['evt'] == evt)
        fig = plt.figure(figsize=(100, 36))
        ax = fig.add_subplot(1, 1, 1)
        H, xedges, yedges = np.histogram2d(data['node'][selection], data['time'][selection], bins=(n_nodes, 1000))
        ax.imshow(H, cmap='hot')
        fig.savefig('heatmap_%s.pdf' % evt)
        fig.savefig('heatmap_%s.png' % evt)

heatmap(sys.argv[1])
