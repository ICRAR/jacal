#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2018
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

import logging
import math

import dlg
from dlg.drop import AppDROP, BarrierAppDROP
from dlg.ddap_protocol import AppDROPStates, DROPStates
from dlg.exceptions import InvalidDropException
import six.moves.cPickle as pickle  # @UnresolvedImport
import six.moves.http_client as httplib  # @UnresolvedImport
import oskar
import spead2
import spead2.recv


logger = logging.getLogger(__name__)

class OSKAR2SpeadReceiver(BarrierAppDROP):
    """Receives data drop a spead stream and writes it into its single output"""

    def initialize(self, **kwargs):
        BarrierAppDROP.initialize(self, **kwargs)

        self._port = self._getArg(kwargs, 'port', None)
        if self._port is None:
            raise InvalidDropException(self, 'port is not set')

        self._stream = spead2.recv.Stream(spead2.ThreadPool(), 0)
        self._stream.add_udp_reader(int(self._port))

        try:
            ip = dlg.utils.get_local_ip_addr()[0][0]
            con = httplib.HTTPConnection('sdp-dfms.ddns.net', 8096)
            con.request('GET', '/reg_receiver?ip=%s' % (ip))
        except:
            logger.exception('Failed to register, will continue anyway')

    def run(self):
        """Run the receiver. Each heap is put in a dictionary and sent to our output"""
        item_group = spead2.ItemGroup()

        for heap in self._stream:
            items = item_group.update(heap)
            data = {item.name: item.value for item in items.values()}
            self.outputs[0].write(pickle.dumps(data))

        self._stream.stop()

class SingleInputStreamingApp(AppDROP):
    """Receives data from its single streaming input and processes it"""

    def dropCompleted(self, uid, drop_state):
        """
        Callback invoked when the DROP with UID `uid` (which is either a
        normal or a streaming input of this AppDROP) has moved to the
        COMPLETED or ERROR state. By default no action is performed.
        """

        logger.info("Input %s has completed, finishing ourselves", uid)

        # We have to control our own state lifecycle
        # There is only one input, and therefore once it completes
        # we declared ourselves completed as well
        if drop_state == DROPStates.COMPLETED:
            self.execStatus = AppDROPStates.FINISHED
            self.outputs[0].setCompleted()
        elif drop_state == DROPStates.ERROR:
            self.execStatus = AppDROPStates.ERROR
            self.outputs[0].setCompleted()
        else:
            raise RuntimeError("Unexpected drop state for input %s: %r" % (uid, drop_state))

    def dataWritten(self, uid, data):
        """
        Callback invoked when `data` has been written into the DROP with
        UID `uid` (which is one of the streaming inputs of this AppDROP).
        By default no action is performed
        """

        # We have to control our own state lifecycle
        if self.execStatus != AppDROPStates.RUNNING:
            logger.info("First data received in flagger, moving to RUNNING state")
            self.execStatus = AppDROPStates.RUNNING

        self.process(pickle.loads(data))

class StreamFlaggerApp(SingleInputStreamingApp):
    """Flags individual chunks of data"""

    def process(self, data):
        data['flagged'] = True
        self.outputs[0].write(pickle.dumps(data))

class StreamCalibratorApp(SingleInputStreamingApp):
    """Accummulates all data, calibrates it, and writes it into a measurement set"""

    HEADER_KEYS = ('freq_inc_hz', 'num_baselines', 'num_channels', 'num_pols',
                   'num_stations', 'phase_centre_ra_deg', 'phase_centre_dec_deg',
                   'time_average_sec', 'time_inc_sec', 'time_start_mjd_utc')
    def __init__(self, *args, **kwargs):
        super(StreamCalibratorApp, self).__init__(*args, **kwargs)
        self._measurement_set = None

    def process(self, data):

        if 'num_channels' in data:
            fname = self.outputs[0].path
            self._header = {k: data[k] for k in self.HEADER_KEYS}
            logger.info("Receiving {} channel(s) starting at {} MHz.".format(
                    data['num_channels'], data['freq_start_hz'] / 1e6))
            if self._measurement_set is None:
                self._measurement_set = oskar.MeasurementSet.create(
                    fname, data['num_stations'],
                    data['num_channels'], data['num_pols'],
                    data['freq_start_hz'], data['freq_inc_hz'])
                self._measurement_set.set_phase_centre(
                    math.radians(data['phase_centre_ra_deg']),
                    math.radians(data['phase_centre_dec_deg']))

        if 'vis' in data:
            vis = data['vis']
            time_inc_sec = self._header['time_inc_sec']
            if data['channel_index'] == 0:
                self._measurement_set.write_coords(
                    self._header['num_baselines'] * data['time_index'],
                    self._header['num_baselines'],
                    vis['uu'], vis['vv'], vis['ww'],
                    self._header['time_average_sec'], time_inc_sec,
                    self._header['time_start_mjd_utc'] * 86400 +
                    time_inc_sec * (data['time_index'] + 0.5))
            self._measurement_set.write_vis(
                self._header['num_baselines'] * data['time_index'],
                data['channel_index'], 1,
                self._header['num_baselines'], vis['amp'])