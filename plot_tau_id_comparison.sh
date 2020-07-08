#!/bin/bash

ERA=$1
WP="Tight"
[[ ! -z $2 ]] && WP=$2

source /cvmfs/cms.cern.ch/cmsset_default.sh
eval `scramv1 runtime -sh`
export PYTHONPATH=$PYTHONPATH:$PWD/Dumbledraw

for EMB in "" "--embedding"
do
    python plot_tau_id_comparison.py -e $ERA $EMB -w $WP
done
