'''helper module to connect between the _context.json file and python code'''

import json

_CTXT = {'coverage_threshold_percent':70,
         'post_count':3,
         'post_buffer_in_seconds':86400,
         'prior_count':3,
         'prior_buffer_in_seconds':86400,
         'reset_all':0}
_READ = []
def _context (name:str):
    '''private function'''
    if not _READ:
        with open ('_context.json', 'rt') as file: _CTXT.update(json.load(file))
        _READ.append (True)
        pass
    return _CTXT[name]

# pylint: disable=missing-function-docstring
def coverage_threshold_percent(): return _context ('coverage_threshold_percent')
def post_count(): return _context ('post_count')
def post_buffer_in_seconds(): return _context ('post_buffer_in_seconds')
def prior_count(): return _context ('prior_count')
def prior_buffer_in_seconds(): return _context ('prior_buffer_in_seconds')
def reset_all(): return bool(_context ('reset_all'))
# pylint: enable=missing-function-docstring
