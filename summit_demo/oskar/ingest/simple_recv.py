# -*- coding: utf-8 -*-
# Receives visibility data using SPEAD and writes it to a Measurement Set or another SPEAD stream.

import logging
import json
import sys
import argparse

from spead_recv import SpeadReceiver


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

    # Set up the SPEAD receiver and run it (see method, above).
    receiver = SpeadReceiver(spead_config)
    receiver.run()


if __name__ == '__main__':
    main()
