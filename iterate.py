#!/usr/bin/env python

'''
From an input AOI, determines all overlapping POEORBS. For each POEORBS along all tracks, or
given input tracks, submits an appropriate enumeration job.
'''

from past.builtins import basestring
import sys
import json
import requests
from datetime import datetime
import dateutil.parser
import numpy as np
from hysds.celery import app
import submit_job

def main():
    ctx = load_context()
    queue = ctx.get('enumerator_queue', 'standard_product-s1gunw-acq_enumerator')
    enumeration_job_version = ctx.get('enumeration_job_version', 'master')
    aoi = get_aoi(ctx.get('aoi_name'))
    #parse the tracks from context. If none are input, returns [False]
    tracks = parse_tracks(ctx, aoi)
    skip_days = ctx.get('skipDays', 0)
    minmatch = ctx.get('minMatch', 2)
    acquisition_version = ctx.get('acquisition_version')
    #get all precision orbits that intersect the AOI
    poeorbs = get_objects('poeorb', aoi)
    #for each track in input
    for track in tracks:
        print('Querying for track: {}...'.format(track))
        submit_all_jobs(poeorbs, aoi, track, queue, enumeration_job_version, minmatch, acquisition_version, skip_days)
        pass
    return

def submit_all_jobs(poeorbs, aoi, track, queue, version, minmatch, acquisition_version, skip_days):
    '''gets all the covered acquisitions, determine intersects, & submit enum jobs'''
    #get all acquisitions covered by the AOI & optional tracks
    acquisitions = get_objects('acq', aoi, track)
    print('Found {} acquisitions'.format(len(acquisitions)))
    #determine which precision orbits intersect acquisitions
    matching_poeorbs = determine_matching_poeorbs(poeorbs, acquisitions)
    print('Found {} matching poeorbs'.format(len(matching_poeorbs)))
    #submit enumeration jobs for that AOI and track
    for poeorb in matching_poeorbs:
        print('Submitting enumeration job for poeorb: {}'.format(poeorb.get('_id')))
        submit_enum_job(poeorb, aoi, track, queue, version, minmatch, acquisition_version, skip_days)
        pass
    return

def determine_matching_poeorbs(poeorbs, acquisitions):
    '''determines which poeorbs are covered by an acquisition. returns a list of those poeorbs'''
    acq_a_dict, acq_b_dict = build_acq_dict(acquisitions) #make a dict where the key is the starttime
    ma = build_acquisition_matrix(acq_a_dict) #builds a matrix of starttime endtime plots
    mb = build_acquisition_matrix(acq_b_dict)
    matching = {}
    for poeorb in poeorbs:
        starttime = int(dateutil.parser.parse(poeorb.get('_source', {}).get('starttime', False)).strftime('%s'))
        endtime = int(dateutil.parser.parse(poeorb.get('_source', {}).get('endtime', False)).strftime('%s'))
        if poeorb.get('_source', {}).get('metadata', {}).get('platform', False) == 'Sentinel-1A':
            count = ((ma > starttime) & (ma < endtime)).sum()
        else:
            count = ((mb > starttime) & (mb < endtime)).sum()
        if count > 0:
            matching[poeorb.get('_id', False)] = poeorb
    return list(matching.values())

def build_acq_dict(acquisitions):
    '''builds a dict from the input list based on starttime'''
    acq_a_dict = {}
    acq_b_dict = {}
    for acq in acquisitions:
        starttime = int(dateutil.parser.parse(acq.get('_source', {}).get('starttime', False)).strftime('%s'))
        endtime = int(dateutil.parser.parse(acq.get('_source', {}).get('endtime', False)).strftime('%s'))
        if acq.get('_source', {}).get('metadata', {}).get('platform', False) == 'Sentinel-1A':
            acq_a_dict[starttime] = acq
            acq_a_dict[endtime] = acq
        else:
            acq_b_dict[starttime] = acq
            acq_b_dict[endtime] = acq
    return acq_a_dict, acq_b_dict

def build_acquisition_matrix(acq_dict):
    return np.array(list(acq_dict.keys()))

def submit_enum_job(poeorb, aoi, track, queue, job_version, minmatch, acquisition_version, skip_days):
    '''submits an enumeration job for the give poeorb, aoi, & track. if track is false, it does not use that parameter'''
    job_name = "job-standard_product-s1gunw-acq_enumerator"
    priority = 5
    tags = '{}_T{}_enumeration'.format(aoi.get('_id', 'AOI'), track)
    job_params = {
        "aoi_name": aoi.get('_id'),
        "workflow": "orbit_acquisition_enumerator_standard_product.sf.xml",
        "project": "grfn",
        "dataset_version": "v2.0.0",
        "minMatch": minmatch,
        "threshold_pixel": 5,
        "acquisition_version": acquisition_version,
        "track_numbers": str(track),
        "skipDays": skip_days,
        "starttime": poeorb.get('_source', {}).get('starttime', False),
        "endtime": poeorb.get('_source', {}).get('endtime', False),
        "platform": poeorb.get('_source').get('metadata').get('platform'),
        "localize_products": poeorb.get('_source').get('urls')[1]
    }
    submit_job.main(job_name, job_params, job_version, queue, priority, tags)
    return

def get_aoi(aoi_id):
    '''returns the es object corresponding to the aoi_id'''
    grq_ip = app.conf['GRQ_ES_URL'].replace(':9200', '').replace('http://', 'https://')
    grq_url = '{0}/es/{1}/_search'.format(grq_ip, 'grq_*_area_of_interest')
    grq_query = {"query":{"bool":{"must":[{"term":{"id.raw":aoi_id}}]}},"from":0,"size":10}
    results = query_es(grq_url, grq_query)
    if len(results) != 1:
        raise Exception('found none/multiple aois with id: {}'.format(aoi_id))
    return results[0]

def get_objects(object_type, aoi, track=False):
    """returns all objects of the object type that intersect both
    temporally and spatially with the aoi. POEORB doesn't have a spatial query"""
    #determine index
    idx_dct = {'acq': 'grq_*_acquisition-s1-iw_slc',
               'poeorb' : 'grq_*_s1-aux_poeorb'}
    idx = idx_dct.get(object_type)
    starttime = aoi.get('_source', {}).get('starttime')
    endtime = aoi.get('_source', {}).get('endtime')
    location = aoi.get('_source', {}).get('location')
    grq_ip = app.conf['GRQ_ES_URL'].replace(':9200', '').replace('http://', 'https://')
    grq_url = '{0}/es/{1}/_search'.format(grq_ip, idx)
    if object_type == 'acq':
        if track:
            #subset by track  
            grq_query = {"query":{"filtered":{"query":{"geo_shape":{"location": {"shape":location}}},"filter":{"bool":{"must":[{"term":{"metadata.track_number":track}},{"range":{"endtime":{"from":starttime}}},{"range":{"starttime":{"to":endtime}}}]}}}},"from":0,"size":1000}
        else:
            #get all tracks
            grq_query = {"query":{"filtered":{"query":{"geo_shape":{"location": {"shape":location}}},"filter":{"bool":{"must":[{"range":{"endtime":{"from":starttime}}},{"range":{"starttime":{"to":endtime}}}]}}}},"from":0,"size":1000}
    elif object_type == 'poeorb':
        #query for poeorb
        grq_query = {"query":{"filtered":{"filter":{"bool":{"must":[{"range":{"endtime":{"from":starttime}}},{"range":{"starttime":{"to":endtime}}}]}}}},"from":0,"size":1000}
    results = query_es(grq_url, grq_query)
    return results

def query_es(grq_url, es_query):
    '''
    Runs the query through Elasticsearch, iterates until
    all results are generated, & returns the compiled result
    '''
    # make sure the fields from & size are in the es_query
    if 'size' in es_query:
        iterator_size = es_query['size']
    else:
        iterator_size = 1000
        es_query['size'] = iterator_size
    if 'from' in es_query:
        from_position = es_query['from']
    else:
        from_position = 0
        es_query['from'] = from_position
    #run the query and iterate until all the results have been returned
    print('querying: {}\n{}'.format(grq_url, json.dumps(es_query)))
    response = requests.post(grq_url, data=json.dumps(es_query), verify=False)
    #print('status code: {}'.format(response.status_code))
    #print('response text: {}'.format(response.text))
    response.raise_for_status()
    results = json.loads(response.text, encoding='ascii')
    results_list = results.get('hits', {}).get('hits', [])
    total_count = results.get('hits', {}).get('total', 0)
    for i in range(iterator_size, total_count, iterator_size):
        es_query['from'] = i
        #print('querying: {}\n{}'.format(grq_url, json.dumps(es_query)))
        response = requests.post(grq_url, data=json.dumps(es_query), timeout=60, verify=False)
        response.raise_for_status()
        results = json.loads(response.text, encoding='ascii')
        results_list.extend(results.get('hits', {}).get('hits', []))
    return results_list

def parse_tracks(ctx, aoi):
    '''parses tracks into a list of integers from context. Returns False if the list is not supplied
    or is empty'''
    tracks = ctx.get('track_numbers', False)
    if not tracks:
        #attempt to get them from the aoi
        tracks = aoi.get('_source', {}).get('metadata', {}).get('track_number', False)
        if not tracks:
            #run over all tracks
            return [False]
    if isinstance(tracks, str if sys.version_info[0] >= 3 else basestring):
        # if of type string, convert to a list of ints
        tracks = [int(x) for x in set(tracks.split(','))]
    if len(tracks) < 1:
        return [False]
    return tracks

def load_context():
    '''loads the context file into a dict'''
    try:
        context_file = '_context.json'
        with open(context_file, 'r') as fin:
            context = json.load(fin)
        return context
    except:
        raise Exception('unable to parse _context.json from work directory')


if __name__ == '__main__':
    main()
