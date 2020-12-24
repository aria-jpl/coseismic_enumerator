'''encapsulate all that it takes to get an SLC localized'''

import es
import footprint
import json
import orbit
import os

VERSION = 'v0.0'

def load (primaries:[], secondaries:[], iteration:int):
    '''load SLC from DAACs if it is not already here

    This is going to send jobs to a Localizer queue.
    '''
    fps = {'prime':[footprint.convert (acq, orbit.fetch (acq))
                    for acq in primaries],
           'second':[footprint.convert (acq, orbit.fetch (acq))
                     for acq in secondaries]}
    for pfp,pacq in zip(fps['prime'],primaries):
        md_acqlist = {'master_acquisitions':[pacq['id']],
                      'slave_acquisitions':[]}
        for sfp,sacq in zip(fps['second'],secondaries):
            if pfp.Intersection (sfp).Area() > 0:
                md_acqlist['slave_acquisitions'].append (sacq['id'])
                pass
            pass
        label = 'S1-COSEISMIC-GUNW-acq-list-event-iter_' + str(iteration)
        label += '-' + pacq['id']
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
