'''module that orchestrates all of the work
'''

import datetime
import es
import es.request

def initialize (aoi):
    '''add state information that this processing needs

    Check the AOI for the state information. If it does not exist, then add it.
    '''
    if 'event_processing' not in aoi:
        aoi['event_processing'] = {
            'post':{'acqs':[], 'count':0, 'slcs':[], 'threshold':3,
                    'time_blackout_in_seconds':86400},
            'pre':{'acqs':[], 'count':0, 'slcs':[], 'threshold':3,
                   'time_blackout_in_seconds':86400},
            'previous':'',
            }
        td = datetime.timedelta(seconds=aoi['event_processing']['post']['time_blackout_in_seconds'])
        et = datetime.datetime.fromisoformat(aoi['metadata']['eventtime'])
        prev = et + td
        aoi['event_processing']['previous'] = prev.isoformat('T','seconds')+'Z'
        pass
    return

def main():
    '''the main processing block -- find and loop over all active AOIs'''
    for response in es.query (es.request.ALL_ACTIVE_AOI):
        aoi = response['_source']
        initialize (aoi)
        print (aoi)
        pass
    return

if __name__ == '__main__': main()
