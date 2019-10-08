FROM hysds/pge-base:latest

MAINTAINER aria-ops "jlinick@.jpl.nasa.gov"
LABEL description="AOI Enumerator Submitter Container"

RUN pip install numpy

USER ops

COPY . /home/ops/verdi/ops/aoi_enumerator_submitter

# set entrypoint
WORKDIR /home/ops
CMD ["/bin/bash", "--login"]
