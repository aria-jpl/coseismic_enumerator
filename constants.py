'''Common place to hold contants to prevent circular or cyclic imports'''

import datetime

CT = 'coverage_threshold'
EP = 'event_processing'
TBIS = 'time_blackout_in_seconds'

SENTINEL_LAUNCH = datetime.datetime(2014,4,3)

class NoOrbitsAvailable(Exception):
    '''Isolate an exception for when acquisitions arrive prior to orbits'''
    pass

class NotEnoughHistoricalData(Exception):
    '''Isolate an exception for when cannot find historical data for an AOI'''
    pass
