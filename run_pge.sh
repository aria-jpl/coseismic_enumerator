#! /usr/bin/env bash

# source ISCE env
source /opt/isce2/isce_env.sh
export TROPMAP_HOME=$HOME/tropmap

# source environment
source $HOME/verdi/bin/activate
/home/ops/verdi/ops/coseismic_enumerator/iterate.py
