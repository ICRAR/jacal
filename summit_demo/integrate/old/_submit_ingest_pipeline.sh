#!/bin/bash

apps_rootdir="`abspath $this_dir/../../oskar/ingest`"
outdir="$outdir/`date -u +%Y-%m-%dT%H-%M-%S`"
mkdir -p "$outdir"

# Empty the AWS queue
while true; do
	queue_item="`curl -s http://sdp-dfms.ddns.net:8096/get_receiver`"
	if [ "$queue_item" == "NULL" ]; then
		echo "AWS queue is empty, continuing now"
		break
	fi
	echo "AWS queue not empty yet (just removed $queue_item out of it), draining will continue"
done

jid1=`sbatch --ntasks-per-node=1 -o "$outdir"/dlg_receiver.log -N ${receiver_nodes} -t 00:30:00 --parsable -J dlg_receiver $this_dir/dlg_receiver.sh -V "$venv" -o "$outdir" -a "$apps_rootdir" -g ${logical_graph}`
echo Receiver job ID: $jid1
jid2=`sbatch --ntasks-per-node=${gpus_per_node} -o "$outdir"/mpi_sender.log -N ${sender_nodes} -t 00:10:00 --parsable --dependency=after:$jid1 --gres=gpu:${gpus_per_node} -J mpi_sender $this_dir/mpi_oskar_sender.sh -V "$venv" -o "$outdir" -a "$apps_rootdir"`
echo Sender job ID: $jid2
