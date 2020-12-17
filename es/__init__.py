'''Helper package for making Elastic-Search queries in the context of ARIA

Much of the previous code had lots of cut-n-paste for handling the response(s)
from Elastic-Search(ES). The intent is to reduce that cut-n-paste code and work
from a common base here. By no means should this be considered the most
efficient or effective way to work with ES. It is simply a consolidation of
what was found in previous work without reference ES documenation at all.

However, if one was interested in making it more efficient or effective, then
this package would be the place to do that work.
'''

import hysds.celery
import json
import os
import requests

class ElasticSearchError(Exception):
    '''Used to signal that the request to ES failed in some way'''
    pass


# pylint: disable=dangerous-default-value,too-many-arguments
def query (request:{}, index:str='',
           es_from:int=0, size:int=1000, sort:[]=[], aggs:{}={})->[{}]:
    '''perform a query of ES

    request : the query criteria. If a string, then treat as a stngified JSON
              object. Normally this is the JSON object from Tosca.
    index : part of the URL for ES
    from : starting index of found items
    size : number of items to return each call to ES
    sort : ??
    aggs : ??

    The query will return all found objects in a list and JSON decoded.
    '''
    if isinstance (request, str): request = json.loads (request)

    content = {'query':request,
               'from':es_from,
               'size':size,
               'sort':sort,
               'aggs':aggs}

    if os.environ.get ('ARIA_EXTERNAL_TO_CLUSTER', False):
        # In theory, the code below fails in the container and is for running a
        # container outside the walled garden of the cloud
        grq_ip = hysds.celery.app.conf['GRQ_ES_URL']
        grq_ip = grq_ip.replace(':9200', '').replace('http://', 'https://')
        grq_url = '{0}/es/{1}/_search'.format(grq_ip, index)
    else:
        # In theory, the code below here is correct for in cloud
        grq_ip = hysds.celery.app.conf['GRQ_ES_URL']
        grq_url = '{0}/{1}/_search'.format(grq_ip, index)
        pass

    # initialize loop content
    result = []
    total = None
    while total is None or len(result) < total:
        content['from'] = len(result) + es_from
        response = requests.post (grq_url, data=json.dumps(content))
        response.raise_for_status()
        data = json.loads (response.text, encoding='ascii')
        result.extend (data.get('hits', {}).get('hits', []))
        total = data.get('hits', {}).get('total', 0) if total is None else total
        pass
    return result
