'''encapsulate all that it takes to get an SLC localized'''

import datetime
import es
import footprint
import json
import orbit
import os

VERSION = 'v0.0'

def load (aoi:{}, primaries:[], secondaries:[], iteration:int):
    '''load SLC from DAACs if it is not already here

    This is going to send jobs to a Localizer queue.
    '''
    fps = {'prime':[footprint.convert (acq, orbit.fetch (acq))
                    for acq in primaries],
           'second':[footprint.convert (acq, orbit.fetch (acq))
                     for acq in secondaries]}
    for pfp,pacq in zip(fps['prime'],primaries):
        ends = [pacq['endtime']]
        starts = [pacq['starttime']]
        md_acqlist = {'creation':datetime.datetime.utcnow().isoformat('T','seconds')+'Z',
                      'dem_type': '',  # do not know
                      'direction':aoi['metadata']['context']['orbit_direction'],
                      'endtime': '',
                      'job_priority':'',  # do not know
                      'master_acquisitions':[pacq['id']],
                      'platform':'',  # do not know
                      'slave_acquisitions':[],
                      'starttime': '',
                      'tags':['s1-coseismic-gunw'],
                      'track_number':aoi['metadata']['context']['track_number'],
                      'union_geojson':aoi['location']}
        for sfp,sacq in zip(fps['second'],secondaries):
            intersection = pfp.Intersection (sfp)

            if intersection and intersection.Area() > 0:
                ends.append (sacq['endtime'])
                starts.append (sacq['starttime'])
                md_acqlist['slave_acquisitions'].append (sacq['id'])
                pass
            pass
        md_acqlist['endtime'] = sorted (ends)[-1]
        md_acqlist['starttime'] = sorted (starts)[0]
        label = 'S1-COSEISMIC-GUNW-acq-list-event-iter_' + str(iteration)
        label += '-' + pacq['id']
        # Calling es.purge is really only necessary during testing. Once in
        # operations each label should be unique for every run of the enumerator
        # making the call nearly a no-op. Still, it is probably better to leave
        # it in unless one is willing to continuously increase the version.
        es.purge (label, VERSION)

        if not os.path.exists (label): os.makedirs (label, 0o755)

        with open (os.path.join (label, label + '.met.json'), 'tw') as file:
            json.dump (md_acqlist, file, indent=2)
            pass
        with open (os.path.join (label, label + '.dataset.json'), 'tw') as file:
            json.dump ({'id':label, 'label':label, 'version':VERSION},
                       file, indent=2)
            pass
        pass
    return
