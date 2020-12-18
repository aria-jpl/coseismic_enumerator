# Co-Event Enumerator Submitter

Iterates through orbit an determining the relevant co-event AOIs overlaps, then submits enumeration jobs for the matching tracks and AOI.

## Outline of what it does

In a pseudo python form:

```
for aoi in get_active_aoitrack_datasets():

    n = 0

    while aoi['event']['pre']['count'] < aoi['event']['pre']['threshold']:

        acqs = list_of_acquisitions_intersecting(begin=aoi['eventtime'] - (n+1)*6days, end=aoi['event']['time'] - n*6days, location=aoi['location'])


        if enough_coverage (aoi, acqs):

            slcs = load_slcs (acqs)  # should shortcut to nothing because they exist?

            aoi['event']['pre']['acqs'].extend (acqs)

            aoi['event']['pre']['slcs'].extend (slcs)

            aoi['event']['pre']['count'] += 1

            pass


        n += 1

        pass

    acqs = list_of_acquisitions_intersecting (begin=aoi['previous'], end=utcnow(), location=aoi['location'])


    if not enough_coverage (aoi, acqs): exit  # need to define when there is enough coverage to include bad acqs


    eofs = load_orbits (aoi['pre-event']['acqs'] + acqs)

    slcs = load_slcs (acqs)  # this may shuffle it off to a different queue for other jobs to do
    
    aoi['previous'] = utcnow()
    save_aoi_to_es (aoi)
    '''
```

## Some static analysis

### Tool
```
pylint --version
pylint 2.4.4
astroid 2.3.3
Python 3.8.5 (default, Jul 28 2020, 12:59:40) 
[GCC 9.3.0]
```

### Command
```
pylint -d C0321,C0326,C0411,W0107,R1711 active.py context.py footprint.py iterate.py orbit.py slc.py test.py es
```

### Latest Result
```
************* Module active
active.py:135:2: W0511: FIXME: need to update AOI in ES (fixme)
************* Module footprint
footprint.py:17:2: W0511: FIXME: should actually do commented out code (fixme)
************* Module iterate
iterate.py:42:2: W0511: FIXME: active.process() should be in a try catch block for when there (fixme)

------------------------------------------------------------------
Your code has been rated at 9.91/10 (previous run: 9.91/10, +0.00)
```
