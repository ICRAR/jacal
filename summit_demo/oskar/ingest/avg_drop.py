import json
import logging
import os
import os.path as osp
import time

from multiprocessing import Lock
from threading import Thread

from dlg.drop import AppDROP, BarrierAppDROP
from dlg.ddap_protocol import AppDROPStates
from dlg import utils

from spead_recv import SpeadReceiver

import six.moves.http_client as httplib


logger = logging.getLogger(__name__)

def get_ip_via_netifaces(loc=''):
    return utils.get_local_ip_addr()[1][0]

def register_my_ip(mydrop_name):
     # register IP address for sender/relay receiver to use (we hardcode port for now, thus one sender one receiver pair)
    public_ip = get_ip_via_netifaces()
    ip_adds = '{0}{1}'.format(public_ip, "")
    origin_ip = ip_adds.split(',')[0]
    logger.info('%s Register IP address %s to AWS' % (mydrop_name, origin_ip))
    cmd_ip='curl http://sdp-dfms.ddns.net:8096/reg_receiver?ip=%s' % origin_ip
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
        self.use_aws_ip = bool(kwargs.get('use_aws_ip', 1))
        self.disconnect_tolerance = int(kwargs.get('disconnect_tolerance', 0))

        with open(kwargs['config']) as f:
            self.config = json.load(f)

        if self.config['as_relay'] == 1:
            raise Exception('Running as a relay configuration.')
        self.config_dir = osp.dirname(kwargs['config'])
        root_dir = osp.abspath(osp.join(self.config_dir, '..'))
        ff = self.config['baseline_map_filename']
        self.config['baseline_map_filename'] = osp.join(root_dir, ff)
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
                logger.info("AveragerSinkDrop SpeadReceiver")
                if (self.use_aws_ip):
                   register_my_ip(self.name)
                self.config['output_ms'] = self.outputs[0].path
                self.recv = SpeadReceiver(self.config, self.disconnect_tolerance)
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
            #self.recv.close()
            self.recv_thread.join()


class AveragerRelayDrop(BarrierAppDROP):

    def initialize(self, **kwargs):
        self.recv = None
        self.recv_thread = None

        with open(kwargs['config']) as f:
            self.config = json.load(f)

        if self.config['as_relay'] == 0:
            raise Exception('Not running as a relay configuration.')

        self.use_aws_ip = bool(kwargs.get('use_aws_ip', 1))
        self.disconnect_tolerance = int(kwargs.get('disconnect_tolerance', 0))
        super(AveragerRelayDrop, self).initialize(**kwargs)

    def run(self):
        logger.info("Running AveragerRelayDrop")
        # write will block until dataWritten in AveragerSinkDrop returns
        logger.debug("Triggering AveragerSinkDrop to start")
        self.outputs[0].write(b'init')
        logger.debug("AveragerSinkDrop started")

        if (self.use_aws_ip):
            host = _get_receiver_host()
            if host != 'NULL':
                old_host = self.config['relay']['stream']['host']
                self.config['relay']['stream']['host'] = host
                logger.info("Ignore the host %s in JSON, relay to %s instead" % (old_host, host))
            else:
                raise Exception("Could not get AveragerSinkDrop IP from AWS!")
            # registering my IP for sender too
            for _ in self.config['streams']:
                register_my_ip(self.name)

        logger.info("AveragerRelayDrop Starting")
        self.recv = SpeadReceiver(self.config, self.disconnect_tolerance)
        self.recv.run()
        self.recv.close()
        # self.recv_thread = Thread(target=self.recv.run)
        # self.recv_thread.start()
        logger.info("AveragerRelayDrop Finished")

    def close_sink(self):
        if self.recv:
            self.recv.close()
            self.recv_thread.join()
