# Coseismic Enumerator

Iterates through active aoitrack-earthquake datasets and generates acquisition lists formed by SLCs covering the aoitrack-earthquake both prior and post the earthquake event.

## Build Instructions

Built using the ARIA HySDS Jenkins Continuous Integration (CI) pipeline.

More information about this process can be found [here](https://hysds-core.atlassian.net/wiki/spaces/HYS/pages/455114757/Deploy+PGE+s+onto+Cluster)

## Run Instructions

You may run your customized PGE via two methods that are documented below:
- An [on-demand (one-time) job](https://hysds-core.atlassian.net/wiki/spaces/HYS/pages/378601499/Submit+an+On-Demand+Job+in+Facet+Search)


## Release History

## Contributing

#  Below is useful but non-uniform information

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
pylint -d C0321,C0326,C0411,W0107,R1711 active.py context.py footprint.py iterate.py orbit.py slc.py test.py es submit.py
```

### Latest Result
```
--------------------------------------------------------------------
Your code has been rated at 10.00/10 (previous run: 10.00/10, +0.00)

```


## FAQ

1. How often should I run the enumerator through cron?  
    1. On factotum or whatever machine you want to run the enumerator on, clone this repository
    2. Add a cron item like this one which runs every 4 hours  
        `0 */4 * * * $HOME/verdi/bin/python /export/home/hysdsops/verdi/ops/coseismic_enumerator/submit.py main https://100.67.33.56/mozart/api/v0.1/job/submit`
2. What are common expected errors that will cause the enumerator to stop?  
    - There are no errors that should cause the enumerator to stop. There are two errors that are handled by the enumerator but do not prevent it from processing all other AOIs.
3. What is the expected disk usage for this PGE?  
    - Less than 100 MBytes
4. What happens if orbit files are unavailable for AOITracks that the Enumerator is asked to processes?  
    - While it may be rare, it can happen that an acquistion arrives before an orbit file. When no orbit is found that covers an acquistion, an error is raised, caught, and logged. The enumerator then moves on to the next AOI to be processed.
5. How should I manually run the Enumerator for failed AOITracks?  
    - There is no manual or HySDS method for retrying the enumerator if and when it fails. The nature of cron is that it runs periodically. Hence, if a run of the enumerator fails due to a missing orbit, then it will try again on the next period until it the orbit file arrives.
6. How do I find the AOITrack ID associated with a failed Enumerator job?
    - Open up the Enumerator's associated HySDS job `_stdout.txt` file and look for the last AOITrack referenced in that file
7. If the enumerator fails on a particular aoitrack-earthquake, is any data persisted to ES as a result (and would that impact the next iteration / processing job)?  
    - No: HySDS does not ingest any data if detects an error.
8. Does the enumerator process aoitrack-earthquakes via a “round-robin” model - in that it will process the “next” aoitrack-earthquake dataset by starting date, or by some other heuristic?  
    - It processes them in the order returned from ES. No special sorts or other ordering requests are made to ES when requesting the AOI tracks. There is no reason to sort since HySDS sees it as a bulk operation.
9. What are the input datasets of the enumerator?
    - An *AOITrack* Dataset, which is a partition of the original Earthquake polygon into Sentinel-1 tracks. Each of these datasets has further water masked land.
11. What are the ouputs of the enumerator?
    - The outputs are so-called *acquisition lists*. These are composed of a list of reference images (in the current implementation, there will always be 1) and a list of secondary images. These images are Single Look Complex (SLC) images. Each list is collected on two separate dates and will be what is used as input for the interferogram processing. More specifically, each acquisition list will correspond to a unique interferogram.
12. What are the post- and pre-index used in the enumerator and its relation to its acquisition lists outputs (including naming)? For a given earthquake, the requirements dictate that we have *three* dates before the earthquake and *three* dates after the earthquake for comparison and generating interferograms.
13. For each AOITrack, how many acquisition lists can we expect?
