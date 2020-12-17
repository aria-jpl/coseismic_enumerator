#! /usr/bin/env python3
'''module that orchestrates all of the work
'''

import active
import datetime
import es
import es.request

def initialize (aoi):
    '''add state information that this processing needs

    Check the AOI for the state information. If it does not exist, then add it.
    '''
    if active.EP not in aoi:
        aoi[active.EP] = {
            active.CT:70.0,
            'post':{'acqs':[], 'count':0, 'length':3, active.TBIS:86400},
            'pre':{'acqs':[], 'count':0, 'length':3, active.TBIS:86400},
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
    for response in es.query (es.request.ALL_ACTIVE_AOI):
        aoi = response['_source']
        print ('begin:', aoi['id'])
        initialize (aoi)
        # FIXME: active.process() should be in a try catch block for when there
        #        is acquisition data but no matching orbit data which can occur
        #        given they are not downloaded together
        active.process (aoi)
        print ('done:', aoi['id'])
        pass
    return

if __name__ == '__main__': main()
