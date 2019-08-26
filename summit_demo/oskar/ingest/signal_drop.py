import copy
import csv
import json
import logging
import os
import subprocess
import sys
import time

import six
from six.moves import configparser

from threading import Thread
from dlg.drop import BarrierAppDROP

from spead_recv import SpeadReceiver

logger = logging.getLogger(__name__)

this_dir = os.path.abspath(os.path.dirname(__file__))
jacal_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))

def relative_to_me(path):
    return os.path.join(jacal_root, path)


class SignalGenerateAndAverageDrop(BarrierAppDROP):

    def initialize(self, **kwargs):

        # spead inputs
        internal_port = int(kwargs.get('internal_port', 41000))
        self.stream_port = int(kwargs.get('stream_port', 51000))
        self.disconnect_tolerance = int(kwargs.get('disconnect_tolerance', 0))

        # oskar inputs
        self.start_freq = kwargs.get('start_freq')
        self.freq_step = kwargs.get('freq_step')
        self.num_freq_steps = int(kwargs.get('num_freq_steps'))
        self.use_gpus = int(kwargs.get('use_gpus', 0))
        self.telescope_model_path = kwargs.get('telescope_model_path')
        self.sky_model_file_path = kwargs.get('sky_model_file_path')
        self.obs_length = kwargs.get('obs_length', '06:00:00.0')
        self.num_time_steps = int(kwargs.get('num_time_steps', 5))

        # SPEAD send config template
        self.spead_send_conf = {
            "stream_config":
                {
                    "max_packet_size": 1472,
                    "rate": 0.0,
                    "burst_size": 8000,
                    "max_heaps": 4
                },
            "stream":
                {
                    "port": 0,
                    "host": "127.0.0.1"
                },
            "write_ms": 0
        }

        # SPEAD recv and avg local config template
        self.spead_avg_conf = {
            "stream_config":
                {
                    "max_packet_size": 1472,
                    "rate": 0.0,
                    "burst_size": 8000,
                    "max_heaps": 4
                },
            "streams":
                [],
            "as_relay": 1,
            "relay":
                {
                "stream_config":
                    {
                        "max_packet_size": 1472,
                        "rate": 0.0,
                        "burst_size": 8000,
                        "max_heaps": 4
                    },
                "stream":
                    {
                        "port": self.stream_port,
                        "host": ""
                    }
                }

            }

        # OSKAR config
        self.oskar_conf = {
                "General":
                    {
                        "app": "oskar_sim_interferometer",
                        "version": "2.7.0"
                    },
                "simulator":
                    {
                        "max_sources_per_chunk": 50000,
                        "use_gpus": "false",
                        "cuda_device_ids": 0,
                        "num_devices": 1,
                        "double_precision": "false",
                    },
                "sky":
                    {
                        "oskar_sky_model/file": ""
                    },
                "observation":
                    {
                        "phase_centre_ra_deg": 201.0,
                        "phase_centre_dec_deg": -44.0,
                        "start_frequency_hz": 0,
                        "num_channels": 1,
                        "frequency_inc_hz": 0,
                        "start_time_utc": "01-01-2000 20:00:00.0",
                        "length": self.obs_length,
                        "num_time_steps": self.num_time_steps
                    },
                "telescope":
                    {
                        "input_directory": self.telescope_model_path
                    }
                }

        self.relay = None
        self.relay_process = None

        self.spead_send = []
        self.spead_avg_local = []

        sky_model_file_list = self._load_sky_model_file_list(self.sky_model_file_path)

        for i in range(self.num_freq_steps):
            # creating N number of oskar and spead send configs
            spead_conf = copy.deepcopy(self.spead_send_conf)
            spead_conf["stream"]["port"] = internal_port + i

            freq = self.start_freq + (self.freq_step * i)
            oskar_conf = copy.deepcopy(self.oskar_conf)
            oskar_conf["observation"]["start_frequency_hz"] = freq
            oskar_conf["observation"]["frequency_inc_hz"] = self.freq_step
            oskar_conf["simulator"]["cuda_device_ids"] = i
            oskar_conf["simulator"]["use_gpus"] = bool(self.use_gpus)

            # set model file for specific freq
            for sky_model_freq, sky_model_file in sky_model_file_list:
                if sky_model_freq >= freq:
                    oskar_conf["sky"]["oskar_sky_model/file"] = sky_model_file
                    break
            if not oskar_conf["sky"]["oskar_sky_model/file"]:
                oskar_conf["sky"]["oskar_sky_model/file"] = sky_model_file
                logger.warning('Defaulting sky model for freq %f to that of frequency %f',
                               freq, sky_model_freq)

            msg = "Creating OSKAR configuration with frequency start/step = %d / %d, sky model file %s"
            logger.info(msg, freq, self.freq_step, sky_model_file)
            logger.info('Using telescope model %s', self.telescope_model_path)

            self.spead_send.append({"spead": spead_conf, "oskar": oskar_conf})

            # Setting relay incoming streams
            self.spead_avg_local.append({"host": "127.0.0.1", "port": internal_port + i})

        self.spead_avg_conf["streams"] = self.spead_avg_local

        super(SignalGenerateAndAverageDrop, self).initialize(**kwargs)

    # list of csv values, each line is freq, abs_path_model_file
    def _load_sky_model_file_list(self, file_path):
        file_map = []
        with open(file_path) as csvfile:
            read_csv = csv.reader(csvfile, delimiter=',')
            for row in read_csv:
                file_map.append((int(row[0]), relative_to_me(row[1])))
        return sorted(file_map, key=lambda kv: kv[0])

    def run(self):
        logger.info("SignalDrop Starting")

        # HACK HACK HACK
        # HACK HACK HACK
        oskar_log_dir = '.'
        try:
            for h in logging.root.handlers:
                if isinstance(h, logging.FileHandler):
                    oskar_log_dir = os.path.dirname(h.baseFilename)
                    break
        except:
            pass
        # HACK HACK HACK
        # HACK HACK HACK


        # assume a downstream AveragerSinkDrop
        self.outputs[0].write(b'init')

        # should be the IP address of the AveragerSinkDrop
        ip_address_sink = self.outputs[0].get_consumers_nodes()[0]

        self.spead_avg_conf["relay"]["stream"]["host"] = ip_address_sink
        self.spead_avg_conf["relay"]["stream"]["port"] = self.stream_port

        # pass this IP addr to spread relay config
        self.relay = SpeadReceiver(spead_config=self.spead_avg_conf,
                                   disconnect_tolerance=self.disconnect_tolerance)
        self.relay_thread = Thread(target=self.relay.run, args=())
        self.relay_thread.start()

        oskar_process_args = []
        for i, conf in enumerate(self.spead_send):
            conf_path = os.path.join(oskar_log_dir, 'oskar_sim_%d.ini' % i)
            spead_conf_path = os.path.join(oskar_log_dir, 'oskar_spead_%d.json' % i)
            # An empty log_file means the underlying OSKAR process will not
            # produce a file with the logs, which is what we want during
            # interactive runs
            log_file = ''
            if oskar_log_dir != '.':
                log_file = os.path.join(oskar_log_dir, 'oskar_%d.log' % i)
            if six.PY3:
                parser = configparser.ConfigParser()
                parser.read_dict(conf['oskar'])
                with open(conf_path, 'w') as conf_file:
                    parser.write(conf_file, space_around_delimiters=False)
            else:
                with open(conf_path, 'w') as conf_file:
                    for section_name, section_dict in conf['oskar'].items():
                        conf_file.write('[%s]\n' % section_name)
                        for name, value in section_dict.items():
                            conf_file.write('%s=%s\n' % (name, str(value)))
            with open(spead_conf_path, 'w') as spead_conf_file:
                json.dump(conf['spead'], spead_conf_file)
            args = [spead_conf_path, conf_path, log_file]
            oskar_process_args.append(args)

        oskar_process = []
        for oskar_args in oskar_process_args:
            p = subprocess.Popen([sys.executable, '-msignal_drop'] + oskar_args,
                                 shell=False, close_fds=True)
            oskar_process.append(p)

        for oskar in oskar_process:
            ecode = oskar.wait()
            logger.info('OSKAR process %d exited with code %d', oskar.pid, ecode)

        self.relay_thread.join()
        self.relay.close()

        logger.info("SignalDrop Finished")

def run_oskar(spead_config, oskar_config_path, oskar_log_file):

    from oskar import SettingsTree
    from spead_send import SpeadSender

    fmt = '%(asctime)-15s %(name)s#%(funcName)s:%(lineno)s %(message)s'
    fmt = logging.Formatter(fmt)
    fmt.converter = time.gmtime
    if oskar_log_file:
        handler = logging.FileHandler(oskar_log_file)
    else:
        handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(fmt)
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)

    logger.info("Starting SpeadSender in process with pid=%d", os.getpid())
    try:
        oskar = SpeadSender(spead_config=spead_config,
                            oskar_settings=SettingsTree("oskar_sim_interferometer",
                                                        settings_file=oskar_config_path))
        oskar.run()
    except:
        logger.exception('Error when running OSKAR, returning with 1')
        sys.exit(1)
    if oskar.abort:
        sys.exit(2)

if __name__ == '__main__':
    # Called from the signal drop to start OSKAR
    spead_conf_path, oskar_config_path, oskar_log_file = sys.argv[1:4]
    with open(spead_conf_path, 'r') as spead_conf_file:
        spead_config = json.load(spead_conf_file)
    run_oskar(spead_config, oskar_config_path, oskar_log_file)