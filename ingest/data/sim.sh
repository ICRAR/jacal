#!/bin/bash -l

export AIPSPATH=$ASKAP_ROOT/Code/Base/accessors/current

$ASKAP_ROOT/Code/Components/Synthesis/synthesis/current/apps/csimulator.sh -c simulator_ade1card.in | tee output_ade1card.out
#$ASKAP_ROOT/Code/Components/Synthesis/synthesis/current/apps/csimulator.sh -c simulator_ade2cards.in | tee output_ade2cards.out
