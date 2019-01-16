# -*- coding: utf-8 -*-
"""Receives visibility data using SPEAD and writes it to a Measurement Set.

To be used in conjunction with spead_send.py in `python/examples/spead/sender`.
Launch this script before the sender to avoid missing any data.

Usage: python spead_recv.py <port> <output_root_name>

The command line arguments are:
    - port:             The UDP port number on which to listen.
    - output_root_name: The root name of the Measurement Set to write.
                        The port number and ".ms" suffixes will be added.
"""

from __future__ import division, print_function
import logging
import json
import math
import sys
import argparse

import oskar
import spead2
import spead2.recv

import numpy as np


def parse_baseline_file(baseline_file):
    baselines = []
    with open(baseline_file) as f:
        for line in f:
            if line.startswith('#'):
                continue
            coord = line.strip('\n')
            if not coord:
                continue
            coord = coord.split(',')
            baselines.append((int(coord[0]), int(coord[1]), int(coord[2])))
    return baselines


class SpeadReceiver(object):
    """Receives visibility data using SPEAD and writes it to a Measurement Set.
    """
    def __init__(self, log, spead_config, file_name, use_adios2):
        self._log = log
        self._streams = []
        self._ports = []
        self.use_adios2 = use_adios2
        self._num_stream = len(spead_config['streams'])

        for recv_config in spead_config['streams']:
            port = recv_config['port']
            stream = spead2.recv.Stream(spead2.ThreadPool(), 0)
            stream.add_tcp_reader(port)
            self._ports.append(port)
            self._streams.append(stream)

        self._measurement_set = None
        self._file_name = file_name
        self._header = {}

        baseline_file = spead_config['averager']['baseline_map_filename']
        self.full_baseline_map = parse_baseline_file(baseline_file)
        self._baseline_exclude = []
        self._baseline_map = []

        index = 0
        for b in self.full_baseline_map:
            if b[2] == 0:
                self._baseline_map.append(b)
            else:
                self._baseline_exclude.append(index)
            index += 1

    def run(self):
        """Runs the receiver."""
        item_group = spead2.ItemGroup()

        # Iterate over all heaps in the stream.
        self._log.info("Waiting to receive on ports {}".format(self._ports))

        running = True
        while running:
            heaps = []
            for stream in list(self._streams):
                try:
                    heap = stream.get()
                    heaps.append(heap)
                except spead2.Stopped:
                    stream.stop()
                    self._streams.remove(stream)

            if len(self._streams) == 0:
                running = False
                continue

            if len(heaps) != self._num_stream:
                raise Exception('Number of streams does not match heaps read')

            datum = []
            for heap in heaps:
                # Extract data from the heap into a dictionary.
                heap_data = {}
                items = item_group.update(heap)
                for item in items.values():
                    heap_data[item.name] = item.value
                datum.append(heap_data)

            data = datum[0]
            # Read the header and create the Measurement Set.
            if 'num_channels' in data:
                self._header = {
                    'freq_start_hz':        data['freq_start_hz'],
                    'freq_inc_hz':          data['freq_inc_hz'],
                    'num_baselines':        data['num_baselines'],
                    'num_channels':         data['num_channels'],
                    'num_pols':             data['num_pols'],
                    'num_stations':         data['num_stations'],
                    'phase_centre_ra_deg':  data['phase_centre_ra_deg'],
                    'phase_centre_dec_deg': data['phase_centre_dec_deg'],
                    'time_average_sec':     data['time_average_sec'],
                    'time_inc_sec':         data['time_inc_sec'],
                    'time_start_mjd_utc':   data['time_start_mjd_utc']
                }
                self._log.info(
                    "Receiving {} channel(s) starting at {} MHz.".format(
                        data['num_channels'], data['freq_start_hz'] / 1e6))
                if self._measurement_set is None:
                    self._measurement_set = oskar.MeasurementSet.create(
                        self._file_name, data['num_stations'],
                        data['num_channels'], data['num_pols'],
                        data['freq_start_hz'], data['freq_inc_hz'],
                        self._baseline_map, use_adios2=self.use_adios2)

                    self._measurement_set.set_phase_centre(
                        math.radians(data['phase_centre_ra_deg']),
                        math.radians(data['phase_centre_dec_deg']))

            # Write visibility data from the SPEAD heap.
            if 'vis' in data:
                vis = data['vis']

                vis_array = np.array([d['vis']['amp'] for d in datum])
                vis_array_sum = vis_array.sum(axis=0)/len(datum)

                # remove unwanted baselines before storing in MS
                num_baselines = self._header['num_baselines'] - len(self._baseline_exclude)

                vis_array_sum_reduced = np.array(
                    [i for j, i in enumerate(vis_array_sum) if j not in self._baseline_exclude])

                time_inc_sec = self._header['time_inc_sec']
                if data['channel_index'] == 0:

                    uu = np.array(
                        [i for j, i in enumerate(vis['uu']) if j not in self._baseline_exclude])
                    vv = np.array(
                        [i for j, i in enumerate(vis['vv']) if j not in self._baseline_exclude])
                    ww = np.array(
                        [i for j, i in enumerate(vis['ww']) if j not in self._baseline_exclude])

                    self._measurement_set.write_coords(
                        num_baselines * data['time_index'],
                        num_baselines,
                        uu, vv, ww,
                        self._header['time_average_sec'], time_inc_sec,
                        self._header['time_start_mjd_utc'] * 86400 +
                        time_inc_sec * (data['time_index'] + 0.5))

                self._measurement_set.write_vis(
                    num_baselines * data['time_index'],
                    data['channel_index'], 1,
                    num_baselines,
                    vis_array_sum_reduced)


def main():
    parser = argparse.ArgumentParser(description='Run Averager.')
    parser.add_argument('--conf', dest='conf', required=True,
                        help='spead configuration json file.')
    parser.add_argument('--out', dest='output', required=True,
                        help='output root name.')
    parser.add_argument('-a', dest='use_adios2', action='store_true', default=False,
                        help='output root name.')

    args = parser.parse_args()

    log = logging.getLogger()
    log.addHandler(logging.StreamHandler(stream=sys.stdout))
    log.setLevel(logging.DEBUG)

    with open(args.conf) as f:
        # Load SPEAD configuration from JSON file.
        spead_config = json.load(f)

    # Append the port number to the output file root path.
    file_name = args.output + ".ms"

    # Use ADIOS2? If we do we need to initialize MPI
    use_adios2 = args.use_adios2
    if use_adios2:
        from mpi4py import MPI

    # Set up the SPEAD receiver and run it (see method, above).
    receiver = SpeadReceiver(log, spead_config, file_name, use_adios2)
    receiver.run()


if __name__ == '__main__':
    main()
