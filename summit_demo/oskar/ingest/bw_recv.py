# -*- coding: utf-8 -*-
# Receives visibility data using SPEAD and writes it to a Measurement Set or another SPEAD stream.

import os
import os.path as osp
import logging
import json
import sys
import argparse

from dlg import utils

from spead_recv import SpeadReceiver
from bw_send import _get_receiver_host


logger = logging.getLogger("ingest")
logger.addHandler(logging.StreamHandler(stream=sys.stdout))
logger.setLevel(logging.DEBUG)


def get_ip_via_netifaces(loc=''):
    return utils.get_local_ip_addr()[1][0]


def main():
    parser = argparse.ArgumentParser(description='Run Averager.')
    parser.add_argument('--conf', dest='conf', required=True,
                        help='spead configuration json file.')

    args = parser.parse_args()
    app_root = osp.abspath(osp.join(args.conf, '..', '..'))

    # Load SPEAD configuration from JSON file.
    with open(args.conf) as f:
        spead_config = json.load(f)
    
    # turn relative paths in json into absolute file paths
    output_ms = osp.join(app_root, spead_config['output_ms'])
    spead_config['output_ms'] = output_ms
    bmf = osp.join(app_root, spead_config['baseline_map_filename'])
    spead_config['baseline_map_filename'] = bmf

    if spead_config['as_relay'] == 1:
        # if I am a relay, obtain the non-relay receiver's IP first, before register my own IP
        # (this behaviour is similar to a sender)
        host = _get_receiver_host()
        if host != 'NULL':
            old_host = spead_config['relay']['stream']['host']
            spead_config['relay']['stream']['host'] = host
            logger.info("Ignore the host %s in JSON, relay to %s instead" % (old_host, host))

    # register IP address for sender/relay receiver to use (we hardcode port for now, thus one sender one receiver pair)
    public_ip = get_ip_via_netifaces()
    ip_adds = '{0}{1}'.format(public_ip, "")
    origin_ip = ip_adds.split(',')[0]
    logger.info('Register IP address %s to AWS' % origin_ip)
    cmd_ip='curl http://sdp-dfms.ddns.net:8096/reg_receiver?ip=%s' % origin_ip
    os.system(cmd_ip)

    # Set up the SPEAD receiver and run it (see method, above).
    receiver = SpeadReceiver(spead_config)
    receiver.run()


if __name__ == '__main__':
    main()
