import json
import logging
import os
import os.path as osp
import time

from multiprocessing import Lock
from threading import Thread

import dlg
from dlg.drop import AppDROP, BarrierAppDROP
from dlg.ddap_protocol import AppDROPStates
from dlg import utils

from spead_recv import SpeadReceiver

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
                    comm = dlg.mpi_comm
                except AttributeError:
                    comm = None
                    if self.use_adios2:
                        import mpi4py
                        comm = mpi4py.MPI.COMM_WORLD

                # Only now we know the correct number of inputs
                self.config['streams'] = [{'host': '0.0.0.0', 'port': self.start_listen_port + i} for i in range(len(self.streamingInputs))]

                logger.info("AveragerSinkDrop SpeadReceiver")

                self.config['output_ms'] = self.outputs[0].path
                self.recv = SpeadReceiver(spead_config=self.config,
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
        with self.lock:
            self.complete_called += 1

        if self.complete_called == len(self.streamingInputs):
            self.close_sink()
            self.execStatus = AppDROPStates.FINISHED

    def close_sink(self):
        if self.recv:
            self.recv_thread.join()


class AveragerRelayDrop(BarrierAppDROP):

    def initialize(self, **kwargs):
        self.recv = None
        self.recv_thread = None

        with open(kwargs['config']) as f:
            self.config = json.load(f)

        if self.config['as_relay'] == 0:
            raise Exception('Not running as a relay configuration.')

        # Misuse translator-generated drop uid to generate unique set of ports
        # for these drops, which sit within a "scatter" LG component, and therefore
        # get a final "/n" suffix different for each instantiation
        offset = int(self.uid.split('/')[-1])
        n_streams = int(kwargs.get('n_streams', 6))
        base_port = int(kwargs.get('base_port', 41000)) + n_streams * offset
        self.recv_ports = [base_port + i for i in range(n_streams)]
        logger.info("Will receive %d streams in TCP ports %r", n_streams, self.recv_ports)

        self.use_aws_ip = bool(kwargs.get('use_aws_ip', 0))
        self.disconnect_tolerance = int(kwargs.get('disconnect_tolerance', 0))
        super(AveragerRelayDrop, self).initialize(**kwargs)

    def run(self):
        logger.info("Running AveragerRelayDrop")
        # write will block until dataWritten in AveragerSinkDrop returns
        logger.debug("Triggering AveragerSinkDrop to start")
        self.outputs[0].write(b'init')
        logger.debug("AveragerSinkDrop started")

        if (self.use_aws_ip):
            endpoint = _get_receiver_host()
            if endpoint != 'NULL':
                old_host = self.config['relay']['stream']['host']
                host, port = endpoint.split(':')
                self.config['relay']['stream']['host'] = host
                self.config['relay']['stream']['port'] = int(port)
                logger.info("Ignore the host %s in JSON, relay to %s instead" % (old_host, endpoint))
            else:
                raise Exception("Could not get AveragerSinkDrop IP from AWS!")
            # registering my IP for sender too
            for port in self.recv_ports:
                register_my_ip(self.name, port)

        logger.info("AveragerRelayDrop Starting")
        self.recv = SpeadReceiver(self.config, self.disconnect_tolerance, ports=self.recv_ports)
        self.recv.run()
        self.recv.close()
        # self.recv_thread = Thread(target=self.recv.run)
        # self.recv_thread.start()
        logger.info("AveragerRelayDrop Finished")

    def close_sink(self):
        if self.recv:
            self.recv.close()
            self.recv_thread.join()
