import glob
import itertools
import multiprocessing
import os
import sys

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

def get_events(logfile):

    events = []
    with open(logfile) as f:
        for i, line in enumerate(f):
            if i == 0:
                start = get_time(line)
            elif 'Sending visibility block' in line:
                events.append((get_time(line) - start, 'send_vis'))
            elif 'Relaying heap to sink' in line:
                events.append((get_time(line) - start, 'relay_heap'))
            elif 'Creating standard MS' in line:
                events.append((get_time(line) - start, 'ms_creating'))
            elif 'Measurement Set created' in line:
                events.append((get_time(line) - start, 'ms_created'))
            elif 'Writing visibilities to Measurement Set' in line:
                events.append((get_time(line) - start, 'ms_write'))
            elif 'Closing measurement set' in line:
                events.append((get_time(line) - start, 'ms_closing'))
            elif 'Measurement set closed' in line:
                events.append((get_time(line) - start, 'ms_closed'))

    node = os.path.basename(os.path.dirname(logfile))
    return [(node, t, evt) for t, evt in events]

def main(input_dir):

    all_logs = glob.glob(os.path.join(input_dir, '*', 'dlgNM.log'))
    events = multiprocessing.Pool().map(get_events, all_logs)
    events = itertools.chain(*events)
    for node, t, evt in events:
        print("%s %f %s" % (node, t, evt))

main(sys.argv[1])
