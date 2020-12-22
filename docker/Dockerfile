FROM hysds/isce2:v2.3.3-es1

MAINTAINER aria-ops "jlinick@.jpl.nasa.gov"
LABEL description="Coseismic Enumerator Container"

# copy packages
COPY . /home/ops/verdi/ops/coseismic_enumerator
RUN set -ex \
 && source /home/ops/verdi/bin/activate \
 && source /opt/isce2/isce_env.sh \
 && sudo chown -R ops:ops /home/ops/verdi/ops/coseismic_enumerator \
 && cd /home/ops/verdi/ops/coseismic_enumerator

# set entrypoint
USER ops
WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
