FROM hysds/isce2:v2.3.3-es1

MAINTAINER aria-ops "jlinick@.jpl.nasa.gov"
LABEL description="CO-Event Enumerator Submitter Container"

# copy packages
COPY . /home/ops/verdi/ops/coevent_enumerator_submitter
RUN set -ex \
 && source /home/ops/verdi/bin/activate \
 && source /opt/isce2/isce_env.sh \
 && sudo chown -R ops:ops /home/ops/verdi/ops/coevent_enumerator_submitter \
 && cd /home/ops/verdi/ops/coevent_enumerator_submitter

# set entrypoint
USER ops
WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
