'''encapsulate all that it takes to get an orbit'''

import datetime
import es.request
import isce  # pylint: disable=unused-import
import os

from isceobj.Sensor.TOPS.BurstSLC import BurstSLC
from isceobj.Sensor.TOPS.Sentinel1 import Sentinel1 as Sentinel

def extract (begin:str, end:str, orbit:Sentinel)->BurstSLC:
    '''Function that will extract the sentinel-1 state vector information

    from the orbit files and populate a ISCE sentinel-1 product with the state
    vector information.
    '''
    # ISCE internals read the required time-period to be extracted from the
    # orbit using the sentinel-1 product start and end-times.
    # Below we will add a dummy burst with the user-defined start and end-time
    # and include it in the sentinel-1 product object.
    #
    # Create empty burst SLC
    burst = BurstSLC()  # see import statements as this an ISCE object
    burst.configure()
    burst.burstNumber = 1
    burst.sensingStart=datetime.datetime.fromisoformat(begin[:-1])
    burst.sensingStop=datetime.datetime.fromisoformat(end[:-1])
    orbit.product.bursts = [burst]
    orb = orbit.extractPreciseOrbit()
    for state_vector in orb: burst.orbit.addStateVector(state_vector)
    return burst

def fetch (acquisition:dict)->{}:
    '''load orbit files of highest precision for given acquisition'''
    sat = acquisition['id'].split('-')[1].split('_')[0]
    orb = es.query (es.request.pair_acquisition_with_orbit
                    (acquisition['starttime'], acquisition['endtime']))
    mat = [o['_id'].startswith (sat) for o in orb]

    if not orb and not any(mat):
        orb = es.query (es.request.pair_acquisition_with_orbit
                        (acquisition['starttime'],acquisition['endtime'],True))
        mat = [o['_id'].startswith (sat) for o in orb]
        pass

    if not orb and not any(mat): raise RuntimeError('No orbits could be found')

    return orb[mat.index(True)]['_source']

def load (eof:dict)->Sentinel:
    '''load the file if not already available and return an ISCE object'''
    filename = eof['id'] + '.EOF'

    if not os.path.isfile (filename):
        url = eof['urls'][[s[:4] for s in eof['urls']].index ('s3:/')]
        url = os.path.join (url, filename)
        print(url)
        pass

    # initiate a Sentinel-1 product instance
    sentinel = Sentinel()  # see import statements as this an ISCE object
    sentinel.configure()
    sentinel.orbitFile = filename
    print("Orbit File : %s" % filename)
    return sentinel

def test():
    '''simple unit test'''
    acq = {'id':'a-S1A_OPER_PREORB-b',
           'starttime':'2020-09-01T01:00:00Z',
           'endtime':'2020-09-01T02:00:00Z'}
    orb = fetch(acq)
    expected = 'S1A_OPER_AUX_POEORB_OPOD_20200921T121449_V20200831T225942'
    expected += '_20200902T005942-v1.1'
    if orb['id'] == expected: print ('preorb check passed')
    else: print ('preorb check FAILED')
    return
