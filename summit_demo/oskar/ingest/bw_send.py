# -*- coding: utf-8 -*-
"""Simulates visibility data using OSKAR and sends it using SPEAD.
"""
import os.path as osp
import logging
import json
import sys
import argparse
import six.moves.http_client as httplib
import oskar

from spead_send import SpeadSender


logger = logging.getLogger("ingest")


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


def main():
    parser = argparse.ArgumentParser(description='Run Averager.')
    parser.add_argument('--conf', dest='conf', required=True,
                        help='spead configuration json file.')

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    from mpi4py import MPI
    args = parser.parse_args()
    conf = args.conf % (MPI.COMM_WORLD.Get_rank() + 1)
    app_root = osp.dirname(osp.dirname(osp.abspath(conf)))

    # Load SPEAD configuration from JSON file.
    with open(conf) as f:
        spead_config = json.load(f)

    endpoint = _get_receiver_host()
    if endpoint != 'NULL':
        old_host = spead_config['stream']['host']
        host, port = endpoint.split(':')
        spead_config['stream']['host'] = host
        spead_config['stream']['port'] = int(port)
        logger.info("Ignore the host %s in JSON, use new endpoint %s instead" % (old_host, endpoint))

    # Load the OSKAR settings INI file for the application.
    ini_path = osp.join(app_root, spead_config["simulation"])
    settings = oskar.SettingsTree('oskar_sim_interferometer', ini_path)
    spead_config["simulation"] = ini_path
    logger.info('init path = %s' % ini_path)

    # Set up the SPEAD sender and run it (see method, above).
    sender = SpeadSender(spead_config, oskar_settings=settings)
    sender.run()


if __name__ == '__main__':
    main()
