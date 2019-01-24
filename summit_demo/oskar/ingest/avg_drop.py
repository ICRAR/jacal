import json
import logging

from multiprocessing import Lock
from threading import Thread

from dlg.drop import AppDROP, BarrierAppDROP
from dlg.ddap_protocol import AppDROPStates

from spead_recv import SpeadReceiver


logger = logging.getLogger(__name__)


class AveragerSinkDrop(AppDROP):

    def initialize(self, **kwargs):
        self.start = False
        self.lock = Lock()
        self.recv = None
        self.recv_thread = None
        self.written_called = 0
        self.complete_called = 0

        with open(kwargs['config']) as f:
            self.config = json.load(f)

        if self.config['as_relay'] == 1:
            raise Exception('Running as a relay configuration.')

        super(AveragerSinkDrop, self).initialize(**kwargs)

    def dataWritten(self, uid, data):
        logger.info("AveragerSinkDrop dataWritten called")

        with self.lock:
            if self.start is False:
                logger.info("AveragerSinkDrop SpeadReceiver")
                self.config['output_ms'] = self.outputs[0].path
                self.recv = SpeadReceiver(self.config)
                self.recv_thread = Thread(target=self.recv.run)
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
            self.recv.close()
            self.recv_thread.join()


class AveragerRelayDrop(BarrierAppDROP):

    def initialize(self, **kwargs):
        self.recv = None
        self.recv_thread = None

        with open(kwargs['config']) as f:
            self.config = json.load(f)

        if self.config['as_relay'] == 0:
            raise Exception('Not running as a relay configuration.')

        super(AveragerRelayDrop, self).initialize(**kwargs)

    def run(self):
        logger.info("Running AveragerRelayDrop")
        # write will block until dataWritten in AveragerSinkDrop returns
        self.outputs[0].write(b'init')
        logger.info("Written into AveragerSinkDrop")

        logger.info("AveragerRelayDrop Starting")
        self.recv = SpeadReceiver(self.config)
        self.recv_thread = Thread(target=self.recv.run)
        self.recv_thread.start()
        logger.info("AveragerRelayDrop Started")

    def close_sink(self):
        if self.recv:
            self.recv.close()
            self.recv_thread.join()