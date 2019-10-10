#
#    ICRAR - International Centre for Radio Astronomy Research
#    (c) UWA - The University of Western Australia, 2015
#    Copyright by UWA (in the framework of the ICRAR)
#    All rights reserved
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston,
#    MA 02111-1307  USA
#
import os
import sys
import uuid
import optparse
import logging
import time

from dlg import tool,graph_loader,droputils
from dlg.drop import dropdict
from dlg.manager import client
from dlg.dropmake import pg_generator

logger = logging.getLogger(__name__)

def memorySpec(uid, **kwargs):
    dropSpec = dropdict({'oid':str(uid), 'type':'plain', 'storage':'memory'})
    dropSpec.update(kwargs)
    return dropSpec 

def directorySpec(uid, **kwargs):
    dropSpec = dropdict({'oid':str(uid), 'type':'container', 'container':'dlg.drop.DirectoryContainer'})
    dropSpec.update(kwargs)
    return dropSpec 

def splitSpec(uid, **kwargs):
    dropSpec = dropdict({'oid':str(uid), 'type':'app', 'app':'dlg_integrate.wsclean.wscleandrop.Split','tw':5})
    dropSpec.update(kwargs)
    return dropSpec

def cleanSpec(uid, **kwargs):
    dropSpec = dropdict({'oid':str(uid), 'type':'app', 'app':'dlg_integrate.wsclean.wscleandrop.WSClean','tw':5})
    dropSpec.update(kwargs)
    return dropSpec

def create_drop_list(options):
    drop_list = []
    split_drop = splitSpec("split-drop",
                    num_of_copies = options.num_splits,
                    niter = options.niter,
                    pol = options.pol,
                    data_column = options.data_column,
                    weight = options.weight,
                    gain = options.gain,
                    scale = options.scale,
                    size = options.size,
                    name = options.name,
                    ms = options.ms,
                    num_channel = options.num_channel)
                
    fits_out_dir = os.path.dirname(options.name)


    for i in range(options.num_splits):
        args_out_drop = memorySpec("args-drop-%d"%(i+1))
        split_drop.addOutput(args_out_drop)
        wsclean_drop = cleanSpec("clean-drop-%d"%(i+1))
        wsclean_drop.addInput(args_out_drop)
        fits_out_drop = directorySpec("fits-out-drop-%d"%(i+1), dirname = fits_out_dir, check_exists = False)
        wsclean_drop.addOutput(fits_out_drop)

        drop_list.append(args_out_drop)
        drop_list.append(wsclean_drop)
        drop_list.append(fits_out_drop)
    start_drop = memorySpec("start")
    split_drop.addInput(start_drop)
    drop_list.append(split_drop)
    drop_list.append(start_drop)
    return drop_list

def gen_pg_spec(drop_list, sessionId, node_list):
    pgtp = pg_generator.MetisPGTP(drop_list, 1, merge_parts=True)
    pgtp.to_gojs_json(visual=False)
    pg_spec = pgtp.to_pg_spec(node_list, num_islands=1)
    return pg_spec

def run_graph(drop_list, options):
    sessionId = 'wsclean-session-' + str(uuid.uuid1())
    node_list = options.nodes.split(",")

    c = client.NodeManagerClient(host=node_list[0], port=options.port)

    pg = gen_pg_spec(drop_list, sessionId, node_list)

    c.create_session(sessionId)
    logger.info("Appending physical graph...")
    c.append_graph(sessionId, pg)
    
    completed_uids = ["start"]
    c.deploy_session(sessionId, completed_uids)
    logger.info("Session %s deployed", sessionId)

if __name__ == '__main__':
    parser = optparse.OptionParser()

    parser.add_option("-i", "--niter", action="store", type="string", default="10",
                      dest="niter", help="Maximum number of clean iterations to perform. Default: 10")

    parser.add_option("-p", "--pol", action="store", type="string", default="I",
                      dest="pol", help="Default: 'I'. Possible values: XX, XY, YX, YY, I, Q, U, V, RR, RL, LR or LL (case insensitive)")
    
    parser.add_option("-d", "--data-column", action="store", type="string", default="CORRECTED_DATA",
                      dest="data_column", help="Default: CORRECTED_DATA if it exists, otherwise DATA will be used.")
    
    parser.add_option("-w", "--weight", action="store", type="string",default="uniform",
                      dest="weight", help="Weightmode can be: natural, uniform, briggs. Default: uniform. When using Briggs' weighting,\
                        add the robustness parameter, like: '-weight briggs_0.5'")
    
    parser.add_option("-g", "--gain", action="store", type="string",
                      dest="gain", default="0.1", help="Cleaning gain: Ratio of peak that will be subtracted in each iteration. Default: 0.1")
    
    parser.add_option("-s", "--scale", action="store", type="string", default="0.01deg",
                      dest="scale", help="Scale of a pixel. Default unit is degrees, but can be specificied, e.g. -scale 20asec. Default: 0.01deg.")
    
    parser.add_option("-z", "--size", action="store", type="string",
                      dest="size", help="<width>_<height> Set the output image size in number of pixels (without padding). Required")
    
    parser.add_option("-n", "--name", action="store", type="string",
                      dest="name", help="Use image-prefix as prefix for output files. Default is 'wsclean'.")

    parser.add_option("-f", "--ms", action="store", type="string",
                      dest="ms", help="Measurements Set files")

    parser.add_option("-c", "--num_channel", action="store", type="string",
                      dest="num_channel", help="number of channels in MS") 

    parser.add_option("-m", "--num_splits", action="store", type="int", default=1,
                      dest="num_splits", help="number of splits")

    parser.add_option("-N", "--nodes", action="store", type="string",default="127.0.0.1,127.0.0.1",
                    dest="nodes", help="nodes list, first node refer to DataIslandManager node")

    parser.add_option("-P", "--port", action="store", type="int",default=8001,
                    dest="port", help="DataIslandManager 's rest port")

    (options, args) = parser.parse_args()
    
    if (None == options.ms or None == options.size):
        parser.print_help()
        sys.exit(1)

    drop_list = create_drop_list(options)
    run_graph(drop_list, options)

    sys.exit(0)
