import os
import csv
import copy
import logging
import configparser

from oskar import SettingsTree
from threading import Thread
from multiprocessing import Process
from dlg.drop import BarrierAppDROP

from spead_recv import SpeadReceiver
from spead_send import SpeadSender

logger = logging.getLogger(__name__)


class SignalGenerateAndAverageDrop(BarrierAppDROP):

    def initialize(self, **kwargs):

        # spead inputs
        self.stream_port = int(kwargs.get('stream_port', 0))
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
        self.use_adios = int(kwargs.get('use_adios', 0))

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
                        "phase_centre_ra_deg": 201.4,
                        "phase_centre_dec_deg": -43.0,
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
        self.oskar_process = []

        self.spead_send = []
        self.spead_avg_local = []

        sky_model_file_list = self._load_sky_model_file_list(self.sky_model_file_path)

        for i in range(self.num_freq_steps):
            # creating N number of oskar and spead send configs
            spead_conf = copy.deepcopy(self.spead_send_conf)
            spead_conf["stream"]["port"] = 41000+i

            freq = self.start_freq+(self.freq_step*i)
            oskar_conf = copy.deepcopy(self.oskar_conf)
            oskar_conf["observation"]["start_frequency_hz"] = freq
            oskar_conf["observation"]["frequency_inc_hz"] = self.freq_step
            oskar_conf["simulator"]["cuda_device_ids"] = i
            oskar_conf["simulator"]["use_gpus"] = bool(self.use_gpus)

            # set model file for specific freq
            for key, value in sky_model_file_list:
                if key >= freq:
                    oskar_conf["sky"]["oskar_sky_model/file"] = value
                    break

            if not oskar_conf["sky"]["oskar_sky_model/file"]:
                raise Exception(f"Could not find sky model for freq {freq}")

            self.spead_send.append({"spead": spead_conf, "oskar": oskar_conf})

            # Setting relay incoming streams
            self.spead_avg_local.append({"host": "127.0.0.1", "port": 41000+i})

        self.spead_avg_conf["streams"] = self.spead_avg_local

        super(SignalGenerateAndAverageDrop, self).initialize(**kwargs)

    # list of csv values, each line is freq, abs_path_model_file
    def _load_sky_model_file_list(self, file_path):
        file_map = []
        with open(file_path) as csvfile:
            read_csv = csv.reader(csvfile, delimiter=',')
            for row in read_csv:
                file_map.append((int(row[0]), row[1]))
        return sorted(file_map, key=lambda kv: kv[0])

    def _start_oskar_process(self, spead_config, oskar_config_path):
        oskar = SpeadSender(spead_config=spead_config,
                            oskar_settings=SettingsTree("oskar_sim_interferometer",
                                                        settings_file=oskar_config_path))
        oskar.run()
        oskar.finalise()

    def run(self):
        logger.info("SignalDrop Starting")

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

        for i, conf in enumerate(self.spead_send):
            conf_path = f"/tmp/sim{i}.ini"
            parser = configparser.ConfigParser()
            parser.read_dict(conf['oskar'])
            with open(conf_path, 'w') as conf_file:
                parser.write(conf_file, space_around_delimiters=False)
            p = Process(target=self._start_oskar_process, args=(conf['spead'], conf_path))
            self.oskar_process.append(p)

        for oskar in self.oskar_process:
            oskar.start()

        for oskar in self.oskar_process:
            oskar.join()

        self.relay_thread.join()
        self.relay.close()

        logger.info("SignalDrop Finished")
