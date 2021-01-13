'''module processes an active AOI

This is the bulk of the pseudo code in the README.md that is inside the
outermost loop. It was separated from iterate.py simply to make is trivial
to move it into its own job mechanism.
'''

import collections
import datetime
import es.request
import footprint
import json
import orbit
import os
import slc

CT = 'coverage_threshold'
EP = 'event_processing'
TBIS = 'time_blackout_in_seconds'

def enough_coverage (aoi, acqs, eofs, version_mismatch=0):
    '''determine if these acquisitions (acqs) are good enough

    - Must determine how much of the AOI location is covered.
        - only care about land
        - any intersection is considered required
        - approximate the footprint from the acquisition and orbit information
    - If all the acquisitions are processed with same version
    '''
    versions = collections.Counter([a['metadata']['processing_version']
                                    for a in acqs])
    result = (len(acqs) - versions.most_common()[0][1]) <= version_mismatch

    if result:
        result = footprint.coverage (aoi, acqs, eofs) >= aoi[EP][CT]
        if not result: print ('->     not enough coverage')
    else: print ('->     too many disparte versions')
    return result

def fill (aoi):
    '''find all of the past acquisitions'''
    begin = datetime.datetime.fromisoformat (aoi['metadata']['eventtime'][:-1])
    begin = begin - datetime.timedelta (seconds=aoi[EP]['pre'][TBIS])
    repeat = datetime.timedelta(days=7)
    step = datetime.timedelta(days=5)
    while aoi[EP]['pre']['count'] < aoi[EP]['pre']['length']:
        print('->   filling',aoi[EP]['pre']['count'],'of',aoi[EP]['pre']['length'])
        acqs = intersection (begin=begin, end=begin+repeat,
                             location=aoi['location'])
        eofs = [orbit.fetch (acq) for acq in acqs]
        begin = begin - step

        if acqs and enough_coverage (aoi, acqs, eofs):
            aoi[EP]['pre']['acqs'].extend ([{'id':a['id'],
                                             'endtime':a['endtime'],
                                             'location':a['location'],
                                             'starttime':a['starttime']}
                                            for a in acqs])
            aoi[EP]['pre']['count'] += 1
            t_0 = sorted ([datetime.datetime.fromisoformat(a['starttime'][:-1])
                           for a in acqs])[0]
            begin = t_0 - datetime.timedelta(days=8)
            update (aoi)
            pass
        pass
    return

def intersection (begin, end, location):
    '''find the list of acquisitions that intersect with the

    begin : start time the aquisition must be within
    end : last time the acquisition must be within
    location : geographic area the acquisition must intersect with

    The center or largest group of them that have less than a day separating
    them should be the one returned. An error/warning message should be sent
    up if there is more than one cluster.
    '''
    data = es.query (es.request.collate_acquisitions(begin, end, location))
    return [d['_source'] for d in data]

def process (aoi):
    '''process the AOI as described by the pseudo code in README.md
    '''
    fill(aoi)
    begin = datetime.datetime.fromisoformat (aoi[EP]['previous'][:-1])
    now = datetime.datetime.utcnow()
    repeat = datetime.timedelta(days=7)
    step = datetime.timedelta(days=5)
    while begin < now and aoi[EP]['post']['count'] < aoi[EP]['post']['length']:
        print ('->   posting', aoi[EP]['post']['count'], 'of',
               aoi[EP]['post']['length'])
        end = begin + repeat
        if now < end: end = now

        acqs = intersection (begin=begin,
                             end=end,
                             location=aoi['location'])
        eofs = [orbit.fetch (acq) for acq in acqs]

        if acqs and enough_coverage (aoi, acqs, eofs):
            aoi[EP]['post']['count'] += 1
            slc.load (acqs, aoi[EP]['pre']['acqs'], aoi[EP]['post']['count'])
            aoi[EP]['post']['acqs'].extend ([{'id':a['id'],
                                              'endtime':a['endtime'],
                                              'location':a['location'],
                                              'starttime':a['starttime']}
                                             for a in acqs])
            t_0 = sorted ([datetime.datetime.fromisoformat(a['endtime'][:-1])
                           for a in acqs])[-1]+datetime.timedelta(seconds=3600)
            aoi[EP]['previous'] = t_0.isoformat('T','seconds')+'Z'

            if aoi[EP]['post']['length'] <= aoi[EP]['post']['count']:
                times = []
                for acq in aoi[EP]['pre']['acqs'] + aoi[EP]['post']['acqs']:
                    times.append (acq['starttime'])
                    times.append (acq['endtime'])
                    pass
                times.sort()
                aoi['endtime'] = times[-1]
                aoi['starttime'] = times[0]
                pass

            update (aoi)
        else: begin += step
        pass
    return

def update (aoi):
    '''write the AOI back out to ES

    Much of the AOI processing updates the the state information and it needs
    to be recorded in ES.
    '''
    # FIXME: need to update AOI in ES not create a zesty-test-data
    label = 'zesty-test-data-' + aoi['id']
    es.purge (label, aoi['version'])

    if not os.path.exists (label): os.makedirs (label, 0o755)

    with open (os.path.join (label, label + '.met.json'), 'tw') as file:
        json.dump (aoi['metadata'], file, indent=2)
        pass
    with open (os.path.join (label, label + '.dataset.json'), 'tw') as file:
        aoi_ds = aoi.copy()
        del aoi_ds['metadata']
        aoi_ds['id'] = label
        aoi_ds['label'] = label
        json.dump (aoi_ds, file, indent=2)
        pass
    return

def test_intersection():
    '''simple unit test'''
    begin = datetime.datetime(2020,9,1,0,0,0)
    end = datetime.datetime(2020,9,8,0,0,0)
    location = { 'type':'polygon',
                 'coordinates':[[[-118.60359191894533,34.163522648722825],
                                 [-118.60359191894533,34.27821226443234],
                                 [-118.4703826904297,34.27821226443234],
                                 [-118.4703826904297,34.163522648722825],
                                 [-118.60359191894533,34.163522648722825]]]}
    acqs = intersection (begin, end, location)
    if len(acqs) == 7: print ('-> intersection test passed')
    else: print ('-> intersection test FAILED')

    starts = [datetime.datetime.fromisoformat (acq['starttime'][:-1]) < end
              for acq in acqs]
    ends = [begin < datetime.datetime.fromisoformat (acq['endtime'][:-1])
            for acq in acqs]
    if sum(starts) == len (starts): print ('-> intersection time passed')
    else: print ('-> intersection time FAILED')
    if sum(ends) == len (ends): print ('-> intersection time passed')
    else: print ('-> intersection time FAILED')
    return
