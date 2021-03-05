#! /usr/bin/env python3
'''Small script to allow coseismic enumerator to be run from cron'''

import json
import requests
import sys

# pylint: disable=invalid-name
job_params = {"coverage_threshold_percent": 90,
              "post_count": 3,
              "post_buffer_in_seconds": 60,
              "prior_count": 3,
              "prior_buffer_in_seconds": 60,
              "reset_all": 0}
job_release = sys.argv[1]
job_type = 'job-enumerator'
queue = 'factotum-job_worker-coseismic-enumerator'
tag_name = ['coseismic-enumerator-cron']
params = {
    'queue': queue,
    'priority': 6,
    'job_name': job_type,
    'tags': json.dumps(tag_name),
    'type': "{}:{}".format(job_type, job_release),
    'params': json.dumps(job_params),
    'enable_dedup': False
}
req = requests.post(sys.argv[2], params=params, verify=False)
req.raise_for_status()
print(req.text)
print(req.json())
