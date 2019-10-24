# -*- coding: utf-8 -*-
# Receives visibility data using SPEAD and writes it to a Measurement Set or another SPEAD stream.

import os
import logging
import math
import socket
import subprocess

import oskar
import spead2
import spead2.recv
import spead2.send

import numpy as np


logger = logging.getLogger(__name__)


class ToleranceReached(Exception):
    pass


class SpeadReceiver(object):
    # Receives visibility data using SPEAD and writes it to a Measurement Set.

    def __init__(self, spead_config, disconnect_tolerance=0, ports=None):
        self.spead_config = spead_config
        self._requested_ports = ports
        self._streams = []
        self._ports = []
        self._num_stream = len(self.spead_config['streams'])
        self._num_stream_disconnect = 0
        self._disconnect_tolerance = disconnect_tolerance
        self._header = {}

    def create_receivers(self):
        # Ports can be given explicitly or taken from the config file
        if not self._requested_ports:
            ports = (c['port'] for c in self.spead_config['streams'])
        for port in ports:
            logger.info('Adding TCP stream reader: port %d', port)
            try:
                stream = spead2.recv.Stream(spead2.ThreadPool(), 0)
                stream.stop_on_stop_item = False
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('', port))
                sock.listen(1)
                stream.add_tcp_reader(sock)
                self._ports.append(port)
                self._streams.append(stream)
            except Exception as e:
                logger.error('Failed adding TCP stream reader: error %s port %d', str(e), port)
                raise

    def close(self, graceful=True):
        for stream in list(self._streams):
            try:
                stream.stop()
            except:
                continue

    def run(self):
        try:
            self._run()
        except ToleranceReached:
            logger.exception("Disconnect tolerance reached")
            raise
        except:
            logger.exception("Unexpected error while receiving data, closing")
        finally:
            self.close()

    def _run(self):
        # Runs the receiver.
        item_group = spead2.ItemGroup()

        # Iterate over all heaps in the stream.
        logger.info("Waiting to receive on ports {}".format(self._ports))

        running = True
        while running:

            logger.debug("Reading one heap from all streams")
            heaps = []
            for stream in list(self._streams):
                try:
                    heap = stream.get()
                    if heap.is_end_of_stream():
                        logger.info("Successfully reached end of stream")
                        stream.stop()
                        self._streams.remove(stream)
                        continue
                    heaps.append(heap)

                except spead2.Stopped:
                    self._num_stream_disconnect += 1
                    tolerance = int((self._num_stream_disconnect/self._num_stream)*100.)
                    logger.warning("Signal stream disconnected")
                    stream.stop()
                    self._streams.remove(stream)

                    if tolerance == 0 or tolerance > self._disconnect_tolerance:
                        for end_stream in list(self._streams):
                            end_stream.stop()
                        raise ToleranceReached()

            if len(self._streams) == 0:
                running = False
                continue

            logger.debug("Putting corresponding heaps together")
            data = []
            for heap in heaps:
                # Extract data from the heap into a dictionary.
                items = item_group.update(heap)
                heap_data = {item.name: item.value for item in items.values()}
                data.append(heap_data)

            # Handle header data and visibility data separately
            first_datum = data[0]
            if 'num_channels' in first_datum:
                self._header = {
                    'freq_start_hz':        first_datum['freq_start_hz'],
                    'freq_inc_hz':          first_datum['freq_inc_hz'],
                    'num_baselines':        first_datum['num_baselines'],
                    'num_channels':         first_datum['num_channels'],
                    'num_pols':             first_datum['num_pols'],
                    'num_stations':         first_datum['num_stations'],
                    'phase_centre_ra_deg':  first_datum['phase_centre_ra_deg'],
                    'phase_centre_dec_deg': first_datum['phase_centre_dec_deg'],
                    'time_average_sec':     first_datum['time_average_sec'],
                    'time_inc_sec':         first_datum['time_inc_sec'],
                    'time_start_mjd_utc':   first_datum['time_start_mjd_utc']
                }
                logger.info("Receiving {} channel(s) starting at {} MHz.".format(
                    first_datum['num_channels'], first_datum['freq_start_hz'] / 1e6))
                self.process_header(data)
            if 'vis' in first_datum:
                self.process_visibilities(data)


class VisibilityRelay(SpeadReceiver):
    # Receives visibility data using SPEAD and relays them

    def __init__(self, spead_config, *args, **kwargs):
        super(VisibilityRelay, self).__init__(spead_config, *args, **kwargs)
        self._relay_stream = None
        self._descriptor = None
        try:
            self.create_relay()
            self.create_receivers()
        except:
            self.close(graceful=False)
            raise


    def create_relay(self):

        # Construct TCP streams and associated item groups.
        stream_config = spead2.send.StreamConfig(
            self.spead_config['relay']['stream_config']['max_packet_size'],
            self.spead_config['relay']['stream_config']['rate'],
            self.spead_config['relay']['stream_config']['burst_size'],
            self.spead_config['relay']['stream_config']['max_heaps'])

        stream = self.spead_config['relay']['stream']
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


    def close(self, graceful=True):
        super(VisibilityRelay, self).close(graceful=graceful)
        if self._relay_stream:
            logger.info("Closing relay stream sender")
            stream, item_group = self._relay_stream
            if graceful:
                try:
                    logger.info("Sending end-of-stream heap through relay stream")
                    stream.send_heap(item_group.get_end())
                except:
                    pass
            self._relay_stream = None


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


    def process_header(self, data):

        first_datum = data[0]
        if self._descriptor is None:
            logger.info('Relying metainformation to relay')
            # remove unwanted baselines before storing in MS
            self._create_heaps(first_datum['num_baselines'])

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

    def process_visibilities(self, data):

        vis_array = np.array([d['vis']['amp'] for d in data])
        vis_array_sum = vis_array.sum(axis=0) / len(data)

        num_baselines = self._header['num_baselines']

        vis_pack = np.zeros((num_baselines,),
                            dtype=self._descriptor['vis']['dtype'])
        vis_pack['amp'] = vis_array_sum

        first_datum = data[0]
        if first_datum['channel_index'] == 0:
            vis_pack['uu'] = first_datum['vis']['uu']
            vis_pack['vv'] = first_datum['vis']['vv']
            vis_pack['ww'] = first_datum['vis']['ww']

        # Update the heap and send it.
        stream, heap = self._relay_stream
        heap['vis'].value = vis_pack
        heap['channel_index'].value = first_datum['channel_index']
        heap['time_index'].value = first_datum['time_index']
        logger.info('Relaying heap to sink')
        stream.send_heap(heap.get_heap())


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


class VisibilityMSWriter(SpeadReceiver):
    # Receives visibility data using SPEAD and writes it to a Measurement Set.

    def __init__(self, spead_config, mpi_comm=None, average=True, *args, **kwargs):
        super(VisibilityMSWriter, self).__init__(spead_config, *args, **kwargs)
        self.mpi_comm = mpi_comm
        self.average = average
        self._measurement_set = None
        self._baseline_exclude = set()
        self._baseline_map = []
        self.use_adios2 = spead_config.get('use_adios2', False)
        self._file_name = spead_config.get('output_ms', 'output.ms')
        baseline_map = spead_config.get('baseline_map_filename', None)

        try:
            try:
                os.mkdir(os.path.dirname(self._file_name))
            except OSError:
                pass
            if baseline_map:
                self.setup_baseline_filtering(baseline_map)
            else:
                self._baseline_map = None
            self.create_receivers()
        except:
            self.close(graceful=False)
            raise

    def setup_baseline_filtering(self, baseline_file):
        full_baseline_map = parse_baseline_file(baseline_file)
        index = 0
        for b in full_baseline_map:
            if b[2] == 0:
                self._baseline_map.append(b)
            else:
                self._baseline_exclude.add(index)
            index += 1
        logger.info('Baseline count: total=%d, used=%d, excluded=%d',
                    len(full_baseline_map), len(self._baseline_map), len(self._baseline_exclude))


    def close(self, graceful=True):
        super(VisibilityMSWriter, self).close(graceful=graceful)
        if self._measurement_set:
            logger.info("Closing measurement set %s", self._file_name)
            self._measurement_set = None
            logger.info("Measurement set closed")
            ms_size = int(subprocess.check_output(['du', '-bs',
                self._file_name]).split()[0])
            logger.info('Measurement set %s volume is %d bytes',
                    self._file_name, ms_size)

    def process_header(self, data):

        first_datum = data[0]

        # check that the number of baselines the user supplied is the same
        # as the simulation baseline count. Only need to do this on the writing of
        # the MS as we don't do baseline exclusion on the relay.
        if self._baseline_map:
            supplied_baseline_count = len(self._baseline_exclude) + len(self._baseline_map)
            if supplied_baseline_count != self._header['num_baselines']:
                raise Exception('User baseline map != simulation baseline count {} != {}'
                                .format(supplied_baseline_count, self._header['num_baselines']))

        num_channels = first_datum['num_channels']
        if self.average:
            num_channels *= len(data)

        is_rank0 = True
        msg = 'Creating %s MS under %s using %d antennas, %d channels'
        args = ('ADIOS' if self.use_adios2 else 'standard', self._file_name,
                first_datum['num_stations'], num_channels)
        self.log(msg, *args)

        if self._measurement_set is None:
            self._measurement_set = oskar.MeasurementSet.create(
                self._file_name, first_datum['num_stations'],
                num_channels, first_datum['num_pols'],
                first_datum['freq_start_hz'], first_datum['freq_inc_hz'],
                self._baseline_map, use_adios2=self.use_adios2,
                mpi_comm=self.mpi_comm)

            self._measurement_set.set_phase_centre(
                math.radians(first_datum['phase_centre_ra_deg']),
                math.radians(first_datum['phase_centre_dec_deg']))
        self.log('Measurement Set created at %s', self._file_name)

    def log(self, msg, *args):
        if self.mpi_comm:
            msg += ' @ rank %d/%d (comm=%s)'
            args += (self.mpi_comm.Get_rank() + 1, self.mpi_comm.Get_size(),
                    self.mpi_comm.Get_name())
        return logger.info(msg, *args)

    def process_visibilities(self, data):

        # Average visibilities (or not)
        if self.average:
            vis_amp = np.array([d['vis']['amp'] for d in data])
            vis_amp = vis_amp.sum(axis=0) / len(data)
            num_channels = 1
        else:
            vis_amp = np.concatenate([d['vis']['amp'] for d in data])
            num_channels = len(data)

        num_baselines = self._header['num_baselines'] - len(self._baseline_exclude)

        if len(self._baseline_exclude) > 0:
            vis_amp = np.array(
                [i for j, i in enumerate(vis_amp) if j not in self._baseline_exclude])

        time_inc_sec = self._header['time_inc_sec']

        first_datum = data[0]
        start_row = first_datum['time_index']
        if self.use_adios2:
            start_row *= self.mpi_comm.Get_size()
            start_row += self.mpi_comm.Get_rank()
        start_row *= num_baselines
        logger.info('Writing %d rows starting at row %d', num_baselines, start_row)
        if first_datum['channel_index'] == 0:
            if self._baseline_exclude:
                uu = np.array(
                    [i for j, i in enumerate(first_datum['vis']['uu']) if j not in self._baseline_exclude])
                vv = np.array(
                    [i for j, i in enumerate(first_datum['vis']['vv']) if j not in self._baseline_exclude])
                ww = np.array(
                    [i for j, i in enumerate(first_datum['vis']['ww']) if j not in self._baseline_exclude])
            else:
                uu = first_datum['vis']['uu']
                vv = first_datum['vis']['vv']
                ww = first_datum['vis']['ww']
            self._measurement_set.write_coords(
                start_row,
                num_baselines,
                uu, vv, ww,
                self._header['time_average_sec'], time_inc_sec,
                self._header['time_start_mjd_utc'] * 86400 +
                time_inc_sec * (first_datum['time_index'] + 0.5))

        logger.info('Writing visibilities for %d channel(s) to Measurement Set', num_channels)
        self._measurement_set.write_vis(
            start_row,
            first_datum['channel_index'], num_channels,
            num_baselines,
            vis_amp)
