'''encapsulate all that it takes to get an SLC localized'''

import context
import datetime
import footprint
import hashlib
import json
import orbit
import os

from constants import EP

VERSION = 'v0.0'

def _make_label (acqlist:{})->str():
    acqlist['full_id_hash'] = hashlib.md5(json.dumps([
        ' '.join (sorted (acqlist['master_scenes'])),
        ' '.join (sorted (acqlist['slave_scenes']))
        ]).encode('utf8')).hexdigest()
    # pylint: disable=line-too-long
    return '-'.join (['S1-COSEISMIC-GUNW-acqlist',
                      acqlist['direction'][:3].lower(),
                      'R{0}S{1}'.format (len (acqlist['master_scenes']),
                                         len (acqlist['slave_scenes'])),
                      'TN{0:03d}'.format(int(acqlist['track_number'])),
                      acqlist['starttime'].replace('-','').replace(':','').replace(' ','T')[:-1],
                      acqlist['endtime'].replace('-','').replace(':','').replace(' ','T')[:-1],
                      'poeorb',
                      acqlist['full_id_hash'][:4]])

def _to_scene_id (acq_id:str)->str: return acq_id.split('-')[1]

def _intersected (aoi:{}, primaries:[], secondaries:[]):
    '''generateration algorithm that any amount of intersection
    '''
    # pylint: disable=too-many-locals
    # This does seem to be the minimal set to get the work done efficiently
    fps = {'prime':[footprint.convert (acq, orbit.fetch (acq))
                    for acq in primaries],
           'second':[footprint.convert (acq, orbit.fetch (acq))
                     for acq in secondaries]}
    for pfp,pacq in zip(fps['prime'],primaries):
        md_acqlist = {'aoi_track_id':aoi['id'],
                      'creation':datetime.datetime.utcnow().isoformat('T','seconds')+'Z',
                      'dem_type': '',  # do not know
                      'direction':aoi['metadata']['event_metadata']['orbit_direction'],
                      'endtime': '',
                      'job_priority':3,  # given to me as sufficient
                      'identifier':'',  # do not know
                      'master_acquisitions':[pacq['id']],
                      'master_scenes':[],
                      'platform':'',  # do not know
                      'post_index':aoi[ EP]['post']['count'] + 1,
                      'pre_index':0,
                      'slave_acquisitions':[],
                      'slave_scenes':[],
                      'starttime': '',
                      'tags':['s1-coseismic-gunw'],
                      'track_number':aoi['metadata']['event_metadata']['track_number'],
                      'union_geojson':aoi['location']}
        for index in set(aoi[ EP]['pre']['index']):
            ends = [pacq['endtime']]
            starts = [pacq['starttime']]
            md_acqlist['pre_index'] = -(index+1)
            md_acqlist['slave_acquisitions'] = []
            for _ignore,sfp,sacq in filter (lambda t,i=index:t[0] == i,
                                            zip(aoi[EP]['pre']['index'],
                                                fps['second'],
                                                secondaries)):
                if footprint.intersection_area (pfp, sfp):
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
            label = _make_label (md_acqlist)

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

def _significantly_intersected (aoi:{}, primaries:[], secondaries:[]):
    '''generateration algorithm that requires a certain amount of intersection
    '''
    # pylint: disable=too-many-locals
    # This does seem to be the minimal set to get the work done efficiently
    fps = {'prime':[footprint.convert (acq, orbit.fetch (acq))
                    for acq in primaries],
           'second':[footprint.convert (acq, orbit.fetch (acq))
                     for acq in secondaries]}
    for pfp,pacq in zip(fps['prime'],primaries):
        md_acqlist = {'aoi_track_id':aoi['id'],
                      'creation':datetime.datetime.utcnow().isoformat('T','seconds')+'Z',
                      'dem_type': '',  # do not know
                      'direction':aoi['metadata']['event_metadata']['orbit_direction'],
                      'endtime': '',
                      'job_priority':3,  # given to me as sufficient
                      'identifier':'',  # do not know
                      'master_acquisitions':[pacq['id']],
                      'master_scenes':[],
                      'platform':'',  # do not know
                      'post_index':aoi[ EP]['post']['count'] + 1,
                      'pre_index':0,
                      'slave_acquisitions':[],
                      'slave_scenes':[],
                      'starttime': '',
                      'tags':['s1-coseismic-gunw'],
                      'track_number':aoi['metadata']['event_metadata']['track_number'],
                      'union_geojson':aoi['location']}
        for index in set(aoi[ EP]['pre']['index']):
            ends = [pacq['endtime']]
            starts = [pacq['starttime']]
            md_acqlist['pre_index'] = -(index+1)
            md_acqlist['slave_acquisitions'] = []
            for _ignore,sfp,sacq in filter (lambda t,i=index:t[0] == i,
                                            zip(aoi[EP]['pre']['index'],
                                                fps['second'],
                                                secondaries)):
                if (footprint.intersection_area (pfp, sfp)/pfp.Area() * 100 >
                        100 - context.coverage_threshold_percent()):
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
            label = _make_label (md_acqlist)

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

def _singular (aoi:{}, primaries:[], secondaries:[]):
    '''generateration algorithm that does not break information apart
    '''
    md_acqlist = {'aoi_track_id':aoi['id'],
                  'creation':datetime.datetime.utcnow().isoformat('T','seconds')+'Z',
                  'dem_type': '',  # do not know
                  'direction':aoi['metadata']['event_metadata']['orbit_direction'],
                  'endtime': '',
                  'job_priority':3,  # given to me as sufficient
                  'identifier':'',  # do not know
                  'master_acquisitions':[pacq['id'] for pacq in primaries],
                  'master_scenes':[],
                  'platform':'',  # do not know
                  'post_index':aoi[ EP]['post']['count'] + 1,
                  'pre_index':0,
                  'slave_acquisitions':[],
                  'slave_scenes':[],
                  'starttime': '',
                  'tags':['s1-coseismic-gunw'],
                  'track_number':aoi['metadata']['event_metadata']['track_number'],
                  'union_geojson':aoi['location']}
    for index in set(aoi[ EP]['pre']['index']):
        ends = [pacq['endtime'] for pacq in primaries]
        starts = [pacq['starttime'] for pacq in primaries]
        md_acqlist['pre_index'] = -(index+1)
        md_acqlist['slave_acquisitions'] = []
        for _ignore,sacq in filter (lambda t,i=index:t[0] == i,
                                    zip(aoi[EP]['pre']['index'],
                                        secondaries)):
            ends.append (sacq['endtime'])
            starts.append (sacq['starttime'])
            md_acqlist['slave_acquisitions'].append (sacq['id'])
            pass
        md_acqlist['master_scenes'] = [_to_scene_id (aid) for aid in
                                       md_acqlist['master_acquisitions']]
        md_acqlist['slave_scenes'] = [_to_scene_id (aid) for aid in
                                      md_acqlist['slave_acquisitions']]
        md_acqlist['endtime'] = sorted (ends)[-1]
        md_acqlist['starttime'] = sorted (starts)[0]
        label = _make_label (md_acqlist)

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

def load (aoi:{}, primaries:[], secondaries:[]):
    '''load SLC from DAACs if it is not already here

    This is going to send jobs to a Localizer queue.
    '''
    i = 3
    if i == 1: _intersected (aoi, primaries, secondaries)
    elif i == 2:
        _significantly_intersected (aoi, primaries, secondaries)
    elif i == 3: _singular (aoi, primaries, secondaries)
    else: raise ValueError('bad configuration')
    return
