# -*- coding: utf-8 -*-
"""Simulates visibility data using OSKAR and sends it using SPEAD.
"""
import logging

import numpy
import oskar
import spead2
import spead2.send


logger = logging.getLogger(__name__)


class SpeadSender(oskar.Interferometer):
    # Simulates visibility data using OSKAR and sends it using SPEAD.
    # Inherits oskar.Interferometer to send data in the process_block() method.
    # SPEAD is configured using a Python dictionary passed to the constructor.

    def __init__(self, spead_config, precision=None, oskar_settings=None):
        oskar.Interferometer.__init__(self, precision, oskar_settings)
        self._streams = []
        self._vis_pack = None
        self._write_ms = spead_config['write_ms']

        # Construct UDP streams and associated item groups.
        stream_config = spead2.send.StreamConfig(
            spead_config['stream_config']['max_packet_size'],
            spead_config['stream_config']['rate'],
            spead_config['stream_config']['burst_size'],
            spead_config['stream_config']['max_heaps'])

        stream = spead_config['stream']
        threads = stream['threads'] if 'threads' in stream else 1
        thread_pool = spead2.ThreadPool(threads=threads)
        logger.info("Creating SPEAD stream for host {} on port {}"
                    .format(stream['host'], stream['port']))
        udp_stream = spead2.send.TcpStream(thread_pool, stream['host'],
                                           stream['port'], stream_config)
        item_group = spead2.send.ItemGroup(
            flavour=spead2.Flavour(4, 64, 40, 0))

        # Append udp_stream and item_group to the stream list as a tuple.
        self._streams.append((udp_stream, item_group))

    def finalise(self):
        # Called automatically by the base class at the end of run().
        oskar.Interferometer.finalise(self)
        # Send the end of stream message to each stream.
        for stream, item_group in self._streams:
            try:
                stream.send_heap(item_group.get_end())
            except:
                continue

    def process_block(self, block, block_index):
        """Sends the visibility block using SPEAD.

        Args:
            block (oskar.VisBlock): The block to be processed.
            block_index (int):      The index of the visibility block.
        """
        # Write the block to any open files (reimplements base class method).
        if self._write_ms:
            self.write_block(block, block_index)

        # Get number of streams and maximum number of channels per stream.
        num_streams = len(self._streams)
        hdr = self.vis_header()
        max_channels_per_stream = (hdr.num_channels_total +
                                   num_streams - 1) // num_streams

        # Initialise SPEAD heaps if required.
        if block_index == 0:
            self._create_heaps(block)

            # Write the header information to each SPEAD stream.
            for stream_index, (_, heap) in enumerate(self._streams):
                channel_start = stream_index * max_channels_per_stream
                channel_end = (stream_index + 1) * max_channels_per_stream - 1
                if channel_end > hdr.num_channels_total - 1:
                    channel_end = hdr.num_channels_total - 1
                heap['freq_inc_hz'].value = hdr.freq_inc_hz
                heap['freq_start_hz'].value = (
                    hdr.freq_start_hz + channel_start * hdr.freq_inc_hz)
                heap['num_baselines'].value = block.num_baselines
                heap['num_channels'].value = 1 + channel_end - channel_start
                heap['num_pols'].value = block.num_pols
                heap['num_stations'].value = block.num_stations
                heap['phase_centre_ra_deg'].value = hdr.phase_centre_ra_deg
                heap['phase_centre_dec_deg'].value = hdr.phase_centre_dec_deg
                heap['time_start_mjd_utc'].value = hdr.time_start_mjd_utc
                heap['time_inc_sec'].value = hdr.time_inc_sec
                heap['time_average_sec'].value = hdr.time_average_sec

        # Loop over all times and channels in the block.
        logger.info("Sending visibility block {}/{}"
                    .format(block_index + 1, self.num_vis_blocks))

        for t in range(block.num_times):
            for c in range(block.num_channels):
                # Get the SPEAD stream for this channel index.
                channel_index = block.start_channel_index + c
                stream_index = channel_index // max_channels_per_stream
                stream, heap = self._streams[stream_index]

                # Pack the visibility data into array of structures,
                # ready for sending.
                self._vis_pack['uu'] = block.baseline_uu_metres()[t, :]
                self._vis_pack['vv'] = block.baseline_vv_metres()[t, :]
                self._vis_pack['ww'] = block.baseline_ww_metres()[t, :]
                self._vis_pack['amp'] = block.cross_correlations()[t, c, :, :]

                # Channel index is relative to the channels in the stream.
                heap['channel_index'].value = (
                    channel_index - stream_index * max_channels_per_stream)

                # Update the heap and send it.
                heap['vis'].value = self._vis_pack
                heap['time_index'].value = block.start_time_index + t
                stream.send_heap(heap.get_heap())

    def _create_heaps(self, block):
        """Create SPEAD heap items based on content of the visibility block.

        Args:
            block (oskar.VisBlock): Visibility block.
        """
        # SPEAD heap descriptor.
        # One channel and one time per heap: num_channels is used to tell
        # the receiver how many channels it will be receiving in total.
        amp_type = block.cross_correlations().dtype.name
        descriptor = {
            'channel_index':        {'dtype': 'i4'},
            'freq_inc_hz':          {'dtype': 'f8'},
            'freq_start_hz':        {'dtype': 'f8'},
            'num_baselines':        {'dtype': 'i4'},
            'num_channels':         {'dtype': 'i4'},
            'num_pols':             {'dtype': 'i4'},
            'num_stations':         {'dtype': 'i4'},
            'phase_centre_ra_deg':  {'dtype': 'f8'},
            'phase_centre_dec_deg': {'dtype': 'f8'},
            'time_average_sec':     {'dtype': 'f8'},
            'time_index':           {'dtype': 'i4'},
            'time_inc_sec':         {'dtype': 'f8'},
            'time_start_mjd_utc':   {'dtype': 'f8'},
            'vis': {
                'dtype': [
                    ('uu', block.baseline_uu_metres().dtype.name),
                    ('vv', block.baseline_vv_metres().dtype.name),
                    ('ww', block.baseline_ww_metres().dtype.name),
                    ('amp', amp_type, (block.num_pols,))
                ],
                'shape': (block.num_baselines,)
            }
        }

        # Allocate array of structures for the packed visibility data.
        self._vis_pack = numpy.zeros((block.num_baselines,),
                                     dtype=descriptor['vis']['dtype'])

        # Add items to the item group based on the heap descriptor.
        for stream, item_group in self._streams:
            for key, item in descriptor.items():
                item_shape = item['shape'] if 'shape' in item else tuple()
                item_group.add_item(
                    id=None, name=key, description='',
                    shape=item_shape, dtype=item['dtype'])

            # Send the start of stream message to each stream.
            stream.send_heap(item_group.get_start())
