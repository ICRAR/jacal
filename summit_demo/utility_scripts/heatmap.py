import glob
import itertools
import multiprocessing
import os
import sys

from matplotlib import pyplot as plt
import numpy as np


def as_int(s):
    if s in ('0', '00', '000'):
        return 0
    if s.startswith('0'):
        return int(s.lstrip('0'))
    return int(s)


def get_time(line):
    parts = line.split()[0:2]
    day = as_int(parts[0].split('-')[2])
    the_time, ms = parts[1].split(',')
    ms = as_int(ms)
    hh, mm, ss = map(lambda x: as_int(x), the_time.split(':'))
    return day * 24 * 3600 + hh * 3600 + mm * 60 + ss + ms/1000.


_events_info = (
    ('Starting SpeadSender in process', 'spead_sender_start'),
    ('Creating OSKAR interferometer', 'oskar_interferometer'),
    ('Creating SPEAD2 stream config', 'send_stream_config'),
    ('Creating SPEAD2 Thread pool', 'spead_send_thread_pool'),
    ('Sending visibility block', 'send_vis'),
    ('Relaying heap to sink', 'relay_heap'),
    ('Creating standard MS', 'ms_creating'),
    ('Measurement Set created', 'ms_created'),
    ('Writing visibilities to Measurement Set', 'ms_write'),
    ('Closing measurement set', 'ms_closing'),
    ('Measurement set closed', 'ms_closed'),
)
def get_events(logfile):

    events = []
    with open(logfile) as f:
        for i, line in enumerate(f):
            if i == 0:
                start = get_time(line)
                continue
            for text, name in _events_info:
                if text in line:
                    events.append((get_time(line) - start, name))
    node = int(os.path.basename(os.path.dirname(logfile)))
    return [(node, t, evt) for t, evt in events]


def _heatmap(nodes, times, node_bins, time_bins, exec_time, suffix='', ):
    print("Producing heatmap%s with %d node bins" % (suffix, node_bins))
    fig = plt.figure(figsize=(time_bins / 10., node_bins / 10.))
    ax = fig.add_subplot(1, 1, 1)
    ax.hist2d(times, nodes, bins=(time_bins, node_bins), cmap='hot')
    ax.set_yticks(np.arange(1, node_bins + 1, 5))
    ax.set_title('Execution time: %.2f [s]' % exec_time, fontsize=50.)
    fig.savefig('heatmap%s.png' % suffix)


def heatmap(n_nodes, nodes, times, events):
    nodes = np.array(nodes)
    times = np.array(times)
    events = np.array(events)
    time_bins = min(1000, np.max(times))
    exec_time = np.max(times)

    _heatmap(nodes, times, n_nodes, time_bins, exec_time)
    for evt in ('send_vis', 'ms_write', 'relay_heap'):
        selection = np.where(events == evt)
        node_bins = n_nodes
        if evt == 'ms_write':
            # ceiling division
            node_bins = (node_bins + 5) / 6
        _heatmap(nodes[selection], times[selection],
                node_bins, time_bins, exec_time, suffix="_%s" % evt)


def main(input_dir):
    nm_logs = glob.glob(os.path.join(input_dir, '*', 'dlgNM.log'))
    n_nodes = len(list(nm_logs))
    oskar_logs = glob.glob(os.path.join(input_dir, '*', 'oskar_*.log'))
    all_logs = nm_logs + oskar_logs
    events = multiprocessing.Pool().map(get_events, all_logs)
    nodes, times, events = zip(*itertools.chain(*events))
    heatmap(n_nodes, nodes, times, events)

main(sys.argv[1])
