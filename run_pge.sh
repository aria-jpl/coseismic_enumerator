#! /usr/bin/env bash

# source ISCE env
source /opt/isce2/isce_env.sh

# include hysds environment
# CANNOT: source $HOME/verdi/bin/activate
# BECAUSE: isce2 is built on 3.7.0 and the $HOME/verdi/bin/activate is 3.7.7
#          which means that the C++ wrappers compiled to interface with isce2
#          are build against a different python binary than hysds was installed
#          with. The code belows steals the hysds stuff from other virtualenv
#          and uses it with the isce2 python environment. With luck, the pure
#          python will be happier than the mixed language compiled stuff.
for dname in $(ls /home/ops/verdi/ops)
do
    if [ -d /home/ops/verdi/ops/${dname} ]
    then
        PYTHONPATH=${PYTHONPATH}:/home/ops/verdi/ops/${dname}
    fi
done
PYTHONPATH=${PYTHONPATH}:/home/ops/verdi/lib/python3.7/site-packages
export PYTHONPATH

# do the actual PGE work
/home/ops/verdi/ops/coseismic_enumerator/iterate.py
ec=$?
echo "iterate exit code: $ec"

# the sleep is to keep the container around for debugging purposes
#sleep 600
exit $ec
