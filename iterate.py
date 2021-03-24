#! /usr/bin/env python3
'''module that orchestrates all of the work
'''

# This is here to prevent too much information from flooding STDOUT
import logging
logging.disable(logging.INFO)

# Quieting down logging then makes pylint unhappy so turning off a check
# pylint: disable=wrong-import-position
import active
import context
import datetime
import es
import es.request
import orbit
import sys
import traceback

from constants import NoOrbitsAvailable
from constants import NotEnoughHistoricalData
# pylint: enable=wrong-import-position

def initialize (aoi):
    '''add state information that this processing needs

    Check the AOI for the state information. If it does not exist, then add it.
    '''
    if active.EP not in aoi or context.reset_all():
        aoi[active.EP] = {
            active.CT:context.coverage_threshold_percent(),
            'post':{'acqs':[], 'count':0, 'index':[],
                    'length':context.post_count(),
                    active.TBIS:context.post_buffer_in_seconds()},
            'pre':{'acqs':[], 'count':0, 'index':[],
                   'length':context.prior_count(),
                   active.TBIS:context.prior_buffer_in_seconds()},
            'previous':'',
            }
        # pylint: disable=invalid-name
        dt = aoi[active.EP]['post']['time_blackout_in_seconds']
        dt = datetime.timedelta(seconds=dt)
        et = datetime.datetime.fromisoformat(aoi['metadata']['eventtime'][:-1])
        prev = et + dt
        # pylint: enable=invalid-name
        aoi[active.EP]['previous'] = prev.isoformat('T','seconds')+'Z'
        active.update (aoi)
        pass
    return

def main():
    '''the main processing block -- find and loop over all active AOIs'''
    for response in  es.query (es.request.ALL_ACTIVE_AOI):
        aoi = response['_source']
        print ('-> begin:', aoi['id'])
        initialize (aoi)
        try: active.process (aoi)
        except NoOrbitsAvailable:
            print ('No orbit file AOI:', aoi['id'], file=sys.stderr)
            traceback.print_exc()
        except NotEnoughHistoricalData:
            print ('Not enough historical data for AOI:', aoi['id'],
                   file=sys.stderr)
            traceback.print_exc()

            if 'tags' in aoi['metadata']:
                aoi['metadata']['tags'].append ('not-enough-history')
            else: aoi['metadata']['tags'] = ['not-enough-history']

            now = datetime.datetime.utcnow().isoformat('T','seconds')+'Z'
            aoi['endtime'] = now
            aoi['starttime'] = now
            active.update (aoi)
            pass
        orbit.cleanup()
        print ('-> done:', aoi['id'])
        pass
    return

if __name__ == '__main__': main()
