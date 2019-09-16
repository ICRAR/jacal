import logging
import os

from multiprocessing import Lock
from threading import Thread

from dlg.drop import AppDROP
from dlg.ddap_protocol import AppDROPStates
from dlg import utils

from spead_recv import VisibilityMSWriter

import six.moves.http_client as httplib


logger = logging.getLogger(__name__)

def get_ip_via_netifaces(loc=''):
    return utils.get_local_ip_addr()[1][0]

def register_my_ip(mydrop_name, port):
    # register IP address for sender/relay receiver to use (we hardcode port for now, thus one sender one receiver pair)
    public_ip = get_ip_via_netifaces()
    ip_adds = '{0}{1}'.format(public_ip, "")
    endpoint = '%s:%d' % (ip_adds.split(',')[0], port)
    logger.info('%s Register IP address %s to AWS' % (mydrop_name, endpoint))
    cmd_ip='curl http://sdp-dfms.ddns.net:8096/reg_receiver?ip=%s' % endpoint
    os.system(cmd_ip)

def _get_receiver_host(queue_host='sdp-dfms.ddns.net', queue_port=8096):
    try:
        con = httplib.HTTPConnection(queue_host, queue_port)
        con.request('GET', '/get_receiver')
        response = con.getresponse()
        #print(response.status, response.reason)
        host = response.read()
        return host
    except Exception as exp:
        logger.error("Fail to get receiver ip from the queue: %s" % str(exp))
        return 'NULL'


class AveragerSinkDrop(AppDROP):

    def initialize(self, **kwargs):
        self.start = False
        self.lock = Lock()
        self.recv = None
        self.recv_thread = None
        self.written_called = 0
        self.complete_called = 0

        self.disconnect_tolerance = int(kwargs.get('disconnect_tolerance', 0))
        self.baseline_exclusion_map_path = kwargs.get('baseline_exclusion_map_path')
        self.start_listen_port = int(kwargs.get('stream_listen_port_start', 51000))
        self.use_adios2 = int(kwargs.get('use_adios2', 0))

        self.config = {
            "stream_config":
                {
                    "max_packet_size": 1472,
                    "rate": 0.0,
                    "burst_size": 8000,
                    "max_heaps": 4
                },
            "as_relay": 0,
            "output_ms": "",
            "baseline_map_filename": self.baseline_exclusion_map_path,
            "use_adios2": self.use_adios2,
            }

        super(AveragerSinkDrop, self).initialize(**kwargs)

    def _run(self):
        try:
            self.recv.run()
        except:
            self.execStatus = AppDROPStates.ERROR

    def dataWritten(self, uid, data):
        logger.info("AveragerSinkDrop dataWritten called")

        with self.lock:
            if self.start is False:

                try:
                    from mpi4py import MPI
                    comm = MPI.COMM_SELF
                except:
                    comm = None

                # Only now we know the correct number of inputs
                self.config['streams'] = [{'host': '0.0.0.0', 'port': self.start_listen_port + i} for i in range(len(self.streamingInputs))]

                logger.info("AveragerSinkDrop SpeadReceiver")

                self.config['output_ms'] = self.outputs[0].path
                self.recv = VisibilityMSWriter(spead_config=self.config,
                                        disconnect_tolerance=self.disconnect_tolerance,
                                        mpi_comm=comm)
                self.recv_thread = Thread(target=self._run)
                self.recv_thread.start()
                self.start = True
                logger.info("AveragerSinkDrop Started")
            self.written_called += 1

        if self.written_called == len(self.streamingInputs):
            logger.info("AveragerSinkDrop in RUNNING State")
            self.execStatus = AppDROPStates.RUNNING

    def dropCompleted(self, uid, drop_state):
        n_inputs = len(self.streamingInputs)
        with self.lock:
            self.complete_called += 1
            move_to_finished = self.complete_called == n_inputs

        if move_to_finished:
            self.close_sink()
            self.execStatus = AppDROPStates.FINISHED
            self._notifyAppIsFinished()

    def close_sink(self):
        if self.recv:
            self.recv_thread.join()
