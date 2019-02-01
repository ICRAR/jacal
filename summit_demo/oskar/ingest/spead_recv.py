# -*- coding: utf-8 -*-
# Receives visibility data using SPEAD and writes it to a Measurement Set or another SPEAD stream.

import os
import logging
import math

import oskar
import spead2
import spead2.recv
import spead2.send

import numpy as np

try:
    from mpi4py import MPI
except:
    pass


logger = logging.getLogger("ingest")


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
    # Receives visibility data using SPEAD and writes it to a Measurement Set.

    def __init__(self, spead_config):
        self._streams = []
        self._ports = []
        self.use_adios2 = spead_config['use_adios2']
        self._num_stream = len(spead_config['streams'])

        # Relay attributes
        self._relay_stream = None
        self._descriptor = None

        for recv_config in spead_config['streams']:
            port = recv_config['port']
            stream = spead2.recv.Stream(spead2.ThreadPool(), 0)
            stream.add_tcp_reader(port)
            self._ports.append(port)
            self._streams.append(stream)

        self._measurement_set = None
        self._file_name = spead_config['output_ms']
        self._header = {}

        try:
            os.mkdir(os.path.dirname(self._file_name))
        except OSError:
            pass

        self._baseline_exclude = []
        self._baseline_map = []

        self.as_relay = False
        if spead_config['as_relay'] == 1:
            self.as_relay = True

        if self.as_relay:
            # NOTE: Don't do baseline exclusion if its a relay  as it shares a codebase with the MS writer
            # which will exclude baselines multiple times causing array dimension mismatches.
            # So as a relay just average and pass on all baselines.

            # Construct TCP streams and associated item groups.
            stream_config = spead2.send.StreamConfig(
                spead_config['relay']['stream_config']['max_packet_size'],
                spead_config['relay']['stream_config']['rate'],
                spead_config['relay']['stream_config']['burst_size'],
                spead_config['relay']['stream_config']['max_heaps'])

            stream = spead_config['relay']['stream']
            threads = stream['threads'] if 'threads' in stream else 1
            thread_pool = spead2.ThreadPool(threads=threads)
            logger.info("Relaying visibilities to host {} on port {}"
                        .format(stream['host'], stream['port']))
            tcp_stream = spead2.send.TcpStream(thread_pool, stream['host'],
                                               stream['port'], stream_config)
            
            item_group = spead2.send.ItemGroup(
                flavour=spead2.Flavour(4, 64, 40, 0))

            # Append udp_stream and item_group to the stream list as a tuple.
            self._relay_stream = (tcp_stream, item_group)
        else:
            baseline_file = spead_config['baseline_map_filename']
            if baseline_file:
                full_baseline_map = parse_baseline_file(baseline_file)

                index = 0
                for b in full_baseline_map:
                    if b[2] == 0:
                        self._baseline_map.append(b)
                    else:
                        self._baseline_exclude.append(index)
                    index += 1

    def close(self):
        for stream in list(self._streams):
            stream.stop()

    def _create_heaps(self, num_baselines):
        # Create SPEAD heap items based on content of the visibility block.
        self._descriptor = {
            'channel_index': {'dtype': 'i4'},
            'freq_inc_hz': {'dtype': 'f8'},
            'freq_start_hz': {'dtype': 'f8'},
            'num_baselines': {'dtype': 'i4'},
            'num_channels': {'dtype': 'i4'},
            'num_pols': {'dtype': 'i4'},
            'num_stations': {'dtype': 'i4'},
            'phase_centre_ra_deg': {'dtype': 'f8'},
            'phase_centre_dec_deg': {'dtype': 'f8'},
            'time_average_sec': {'dtype': 'f8'},
            'time_index': {'dtype': 'i4'},
            'time_inc_sec': {'dtype': 'f8'},
            'time_start_mjd_utc': {'dtype': 'f8'},
            'vis': {
                'dtype': [
                    ('uu', 'float32'),
                    ('vv', 'float32'),
                    ('ww', 'float32'),
                    ('amp', 'complex64', (4,))
                ],
                'shape': (num_baselines,)
            }
        }

        # Add items to the item group based on the heap descriptor.
        stream, item_group = self._relay_stream

        for key, item in self._descriptor.items():
            item_shape = item['shape'] if 'shape' in item else tuple()
            item_group.add_item(id=None, name=key, description='',
                                shape=item_shape, dtype=item['dtype'])

        # Send the start of stream message to each stream.
        stream.send_heap(item_group.get_start())

    def run(self):
        # Runs the receiver.
        item_group = spead2.ItemGroup()

        # Iterate over all heaps in the stream.
        logger.info("Waiting to receive on ports {}".format(self._ports))

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
                logger.info("Receiving {} channel(s) starting at {} MHz.".format(
                    data['num_channels'], data['freq_start_hz'] / 1e6))

                if self.as_relay:
                    if self._descriptor is None:
                        # remove unwanted baselines before storing in MS
                        self._create_heaps(data['num_baselines'] - len(self._baseline_exclude))

                        # Write the header information to each SPEAD stream.
                        _, heap = self._relay_stream
                        heap['freq_inc_hz'].value = self._header['freq_inc_hz']
                        heap['freq_start_hz'].value = self._header['freq_start_hz']
                        heap['num_baselines'].value = self._header['num_baselines']
                        heap['num_channels'].value = self._header['num_channels']
                        heap['num_pols'].value = self._header['num_pols']
                        heap['num_stations'].value = self._header['num_stations']
                        heap['phase_centre_ra_deg'].value = self._header['phase_centre_ra_deg']
                        heap['phase_centre_dec_deg'].value = self._header['phase_centre_dec_deg']
                        heap['time_start_mjd_utc'].value = self._header['time_start_mjd_utc']
                        heap['time_inc_sec'].value = self._header['time_inc_sec']
                        heap['time_average_sec'].value = self._header['time_average_sec']
                else:
                    # check that the number of baselines the user supplied is the same
                    # as the simulation baseline count. Only need to do this on the writing of
                    # the MS as we don't do baseline exclusion on the relay.

                    supplied_baseline_count = len(self._baseline_exclude) + len(self._baseline_map)

                    if supplied_baseline_count != self._header['num_baselines']:
                        raise Exception('User baseline map != simulation baseline count {} != {}'
                                        .format(supplied_baseline_count, self._header['num_baselines']))

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

                num_baselines = self._header['num_baselines'] - len(self._baseline_exclude)

                if len(self._baseline_exclude) == 0:
                    vis_array_sum_reduced = vis_array_sum
                else:
                    vis_array_sum_reduced = np.array(
                        [i for j, i in enumerate(vis_array_sum) if j not in self._baseline_exclude])

                time_inc_sec = self._header['time_inc_sec']

                vis_pack = None
                if self.as_relay:
                    # Allocate array of structures for the packed visibility data.
                    vis_pack = np.zeros((num_baselines,),
                                        dtype=self._descriptor['vis']['dtype'])

                if data['channel_index'] == 0:
                    if len(self._baseline_exclude) == 0:
                        uu = vis['uu']
                        vv = vis['vv']
                        ww = vis['ww']
                    else:
                        uu = np.array(
                            [i for j, i in enumerate(vis['uu']) if j not in self._baseline_exclude])
                        vv = np.array(
                            [i for j, i in enumerate(vis['vv']) if j not in self._baseline_exclude])
                        ww = np.array(
                            [i for j, i in enumerate(vis['ww']) if j not in self._baseline_exclude])

                    if self.as_relay:
                        vis_pack['uu'] = uu
                        vis_pack['vv'] = vv
                        vis_pack['ww'] = ww
                    else:
                        self._measurement_set.write_coords(
                            num_baselines * data['time_index'],
                            num_baselines,
                            uu, vv, ww,
                            self._header['time_average_sec'], time_inc_sec,
                            self._header['time_start_mjd_utc'] * 86400 +
                            time_inc_sec * (data['time_index'] + 0.5))

                if self.as_relay:
                    # Update the heap and send it.
                    stream, heap = self._relay_stream
                    vis_pack['amp'] = vis_array_sum_reduced
                    heap['vis'].value = vis_pack
                    heap['channel_index'].value = data['channel_index']
                    heap['time_index'].value = data['time_index']
                    stream.send_heap(heap.get_heap())
                else:
                    self._measurement_set.write_vis(
                        num_baselines * data['time_index'],
                        data['channel_index'], 1,
                        num_baselines,
                        vis_array_sum_reduced)
