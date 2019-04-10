import logging


logger = logging.getLogger(__name__)

def is_sink(d):
    return d[1]['type'] == 'app' and d[1]['app'] == 'avg_drop.AveragerSinkDrop'

def signal_generation_drops(pg_spec, input_oids):
    for oid in input_oids:
        input_spec = pg_spec[oid]
        yield pg_spec[input_spec['producers'][0]]

def modify_sdg(sdg, i, sink_start_freq, freq_step, channels_per_drop):
    sdg['stream_port'] = 51000 + i
    sdg['start_freq'] = sink_start_freq + freq_step * i
    sdg['freq_step'] = freq_step
    sdg['num_freq_steps'] = channels_per_drop

def modify_sink(pg_spec, sink, start_freq, freq_step, channels_per_drop):
    for i, sdg in enumerate(signal_generation_drops(pg_spec, sink[1]['streamingInputs'])):
        modify_sdg(sdg, i, start_freq, freq_step, channels_per_drop)

def modify_pg(pg_spec, start_freq, freq_step, channels_per_drop):
    logger.info('Modifying PG for correct signal generation/sink behavior')
    start_freq = int(start_freq)
    freq_step = int(freq_step)
    channels_per_drop = int(channels_per_drop)
    pg_spec = {drop_spec['oid']: drop_spec for drop_spec in pg_spec}
    for i, sink in enumerate(filter(is_sink, pg_spec.items())):
        sink_start_freq = start_freq + channels_per_drop * freq_step * i
        modify_sink(pg_spec, sink, sink_start_freq, freq_step, channels_per_drop)

if __name__ == '__main__':
    import argparse
    import json
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('start', help='Global frequency start, in Hz', type=int)
    parser.add_argument('step', help='Individual frequency steps, in Hz', type=int)
    parser.add_argument('channels', help='#channels per drop', type=int)
    opts = parser.parse_args()
    pg_spec = json.load(sys.stdin)
    modify_pg(pg_spec, opts.start, opts.step, opts.channels)
    print(json.dumps(pg_spec, indent=2))