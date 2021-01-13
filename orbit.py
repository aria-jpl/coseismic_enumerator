'''encapsulate all that it takes to get an orbit'''

import datetime
import es.request
import hysds.utils
import isce  # pylint: disable=unused-import
import os

from isceobj.Sensor.TOPS.BurstSLC import BurstSLC
from isceobj.Sensor.TOPS.Sentinel1 import Sentinel1 as Sentinel

class NoOrbitsAvailable(Exception):
    '''Isolate an exception for when acquisitions arrive prior to orbits'''
    pass

def cleanup():
    '''Remove downloaded orbit files so HYSDS does not try to upload them'''
    for dirname in _CACHE:
        for filename in os.listdir (dirname):
            os.unlink (os.path.join (dirname, filename))
            pass
        os.rmdir (dirname)
        pass
    _CACHE.clear()
    return

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

    if not orb and not any(mat): raise NoOrbitsAvailable(acquisition['id'])

    return orb[mat.index(True)]['_source']

_CACHE = {}
def load (eof:dict)->Sentinel:
    '''load the file if not already available and return an ISCE object'''
    filename = os.path.join (eof['id'], eof['id'].split('-')[0] + '.EOF')

    if eof['id'] not in _CACHE:
        print ('->     download remote information')
        url = eof['urls'][[s[:4] for s in eof['urls']].index ('s3:/')]
        hysds.utils.download_file (url, eof['id'])
        print ('->     local file:', filename)

        if not os.path.isfile (filename): raise NoOrbitsAvailable(eof['id'])

        sentinel = Sentinel()  # see import statements as this an ISCE object
        sentinel.configure()
        sentinel.orbitFile = filename
        _CACHE[eof['id']] = sentinel
        pass

    return _CACHE[eof['id']]

def test():
    '''simple unit test'''
    acq = {'id':'a-S1A_OPER_PREORB-b',
           'starttime':'2020-09-01T01:00:00Z',
           'endtime':'2020-09-01T02:00:00Z'}
    orb = fetch(acq)
    expected = 'S1A_OPER_AUX_POEORB_OPOD_20200921T121449_V20200831T225942'
    expected += '_20200902T005942-v1.1'
    if orb['id'] == expected: print ('-> preorb check passed')
    else: print ('-> preorb check FAILED')
    return
