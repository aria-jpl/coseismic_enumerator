FROM hysds/pge-base:latest

MAINTAINER aria-ops "jlinick@.jpl.nasa.gov"
LABEL description="AOI Enumerator Submitter Container"

USER ops

RUN sudo pip install numpy

COPY . /home/ops/verdi/ops/aoi_enumerator_submitter

# set entrypoint
WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
