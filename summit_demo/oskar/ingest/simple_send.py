# -*- coding: utf-8 -*-
"""Simulates visibility data using OSKAR and sends it using SPEAD.
"""
import logging
import json
import sys

import argparse
import oskar

from spead_send import SpeadSender


def main():
    try:
        from mpi4py import MPI
    except:
        pass

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    parser = argparse.ArgumentParser(description='Run Averager.')
    parser.add_argument('--conf', dest='conf', required=True,
                        help='spead configuration json file.')

    args = parser.parse_args()

    # Load SPEAD configuration from JSON file.
    with open(args.conf) as f:
        spead_config = json.load(f)

    # Load the OSKAR settings INI file for the application.
    settings = oskar.SettingsTree('oskar_sim_interferometer', spead_config["simulation"])

    # Set up the SPEAD sender and run it (see method, above).
    sender = SpeadSender(spead_config, oskar_settings=settings)
    sender.run()


if __name__ == '__main__':
    main()
