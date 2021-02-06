'''encapsulate all that it takes to get an SLC localized'''

import datetime
import footprint
import json
import orbit
import os

from constants import EP

VERSION = 'v0.0'

def _to_scene_id (acq_id:str)->str: return acq_id.split('-')[1]

def load (aoi:{}, primaries:[], secondaries:[], iteration:int):
    '''load SLC from DAACs if it is not already here

    This is going to send jobs to a Localizer queue.
    '''
    # pylint: disable=too-many-locals
    # This does seem to be the minimal set to get the work done efficiently
    fps = {'prime':[footprint.convert (acq, orbit.fetch (acq))
                    for acq in primaries],
           'second':[footprint.convert (acq, orbit.fetch (acq))
                     for acq in secondaries]}
    for pfp,pacq in zip(fps['prime'],primaries):
        md_acqlist = {'creation':datetime.datetime.utcnow().isoformat('T','seconds')+'Z',
                      'dem_type': '',  # do not know
                      'direction':aoi['metadata']['context']['orbit_direction'],
                      'endtime': '',
                      'job_priority':3,  # given to me as sufficient
                      'identifier':'',  # do not know
                      'master_acquisitions':[pacq['id']],
                      'master_scenes':[],  # do not know
                      'platform':'',  # do not know
                      'slave_acquisitions':[],
                      'slave_scenes':[],  # do not know
                      'starttime': '',
                      'tags':['s1-coseismic-gunw'],
                      'track_number':aoi['metadata']['context']['track_number'],
                      'union_geojson':aoi['location']}
        for index in set(aoi[ EP]['pre']['indices']):
            ends = [pacq['endtime']]
            starts = [pacq['starttime']]
            md_acqlist['slave_acquisitions'] = []
            for _ignore,sfp,sacq in filter (lambda t,i=index:t[0] == i,
                                            zip(aoi[EP]['pre']['indices'],
                                                fps['second'],
                                                secondaries)):
                intersection = pfp.Intersection (sfp)

                if intersection and intersection.Area() > 0:
                    ends.append (sacq['endtime'])
                    starts.append (sacq['starttime'])
                    md_acqlist['slave_acquisitions'].append (sacq['id'])
                    pass
                pass
            md_acqlist['master_scenes'] = [_to_scene_id (aid) for aid in
                                           md_acqlist['master_acquisitions']]
            md_acqlist['slave_scenes'] = [_to_scene_id (aid) for aid in
                                          md_acqlist['slave_acquisitions']]
            md_acqlist['endtime'] = sorted (ends)[-1]
            md_acqlist['starttime'] = sorted (starts)[0]
            label = 'S1-COSEISMIC-GUNW-acq-list-event-iter_'
            label += 'abc'[index] + 'xyz'[iteration]
            label += '-' + pacq['id']

            if not os.path.exists (label): os.makedirs (label, 0o755)

            with open (os.path.join (label, label + '.met.json'), 'tw') as file:
                json.dump (md_acqlist, file, indent=2)
                pass
            with open (os.path.join (label, label + '.dataset.json'), 'tw') as file:
                json.dump ({'id':label, 'label':label, 'version':VERSION},
                           file, indent=2)
                pass
            pass
        pass
    return
