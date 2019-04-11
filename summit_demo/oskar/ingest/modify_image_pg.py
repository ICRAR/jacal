import logging
import os

logger = logging.getLogger(__name__)


def ms_input(d):
    return d[1]['nm'] == 'MS'


def image_output(d):
    return d[1]['nm'] == 'Image'


def modify_pg(pg_spec, inputs, out_dir):
    logger.info('Modifying PG for correct signal generation/sink behavior')

    pg_spec = {drop_spec['oid']: drop_spec for drop_spec in pg_spec}
    ms_inputs = [ms for i, ms in enumerate(filter(ms_input, pg_spec.items()))]
    image_outputs = [ms for i, ms in enumerate(filter(image_output, pg_spec.items()))]

    for i, in_file in enumerate(inputs.split(" ")):
        ms_inputs[i][1]['filepath'] = in_file
        image_outputs[i][1]['filepath'] = out_dir+"/image_"+os.path.basename(in_file)+".fits"


if __name__ == '__main__':
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inputs', help='MS inputs', type=str, required=True)
    parser.add_argument('-o', '--output_dir', help='Output Dir', type=str, required=True)
    opts = parser.parse_args()
    pg_spec = json.load(sys.stdin)
    modify_pg(pg_spec, opts.inputs, opts.output_dir)
    print(json.dumps(pg_spec, indent=2))