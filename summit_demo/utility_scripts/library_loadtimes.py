import io
import subprocess
import sys

from matplotlib import pyplot as plt
import numpy as np

def load_import_times(fname, modname):
    cmd = "sed -n '/Imported .*%s/ { s/.*Imported .* in //; s/ seconds// p }' %s" % (modname, fname)
    x = subprocess.check_output(cmd, shell=True)
    return np.loadtxt(io.BytesIO(x))


def main():

    load = lambda x: load_import_times(sys.argv[1], x)

    g = load('gevent')
    z = load('zmq')
    r = load('zerorpc')

    label_g = 'gevent'
    label_z = 'zmq'
    label_r = 'zerorpc'

    for data, label in zip([g, z, r], [label_g, label_z, label_r]):
        timeouts = len(np.where(data >= 30)[0])
        print("%d NMs loaded %s" % (len(data), label))
        plt.hist(data, bins=120, log=True, label=label)
        plt.legend()
        plt.text(0.5, 0.8, 'imports > 30 seconds: %d' % timeouts, transform=plt.axes().transAxes)
        plt.savefig('%s.png' % label)
        plt.clf()

    plt.hist([g, z, r], bins=120, log=True, label=[label_g, label_z, label_r])
    plt.savefig('all.png')

if __name__ == '__main__':
    main()
