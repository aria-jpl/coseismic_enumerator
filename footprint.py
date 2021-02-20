'''transact with geo-data and satelite data'''

import datetime
import context
import isce  # pylint: disable=unused-import
import json
import numpy
import orbit
import osgeo.ogr
import traceback
import xml.etree.ElementTree

from isceobj.Sensor.TOPS.BurstSLC import BurstSLC
from isceobj.Util.Poly2D import Poly2D
from mpl_toolkits.basemap import Basemap

def convert (acq, eof=None):
    '''convert an object with ['location'] to a shapely polygon'''
    if eof:
        location = {'coordinates':[track (acq, eof)], 'type':'Polygon'}
        poly = osgeo.ogr.CreateGeometryFromJson(json.dumps(location))
    else: poly = osgeo.ogr.CreateGeometryFromJson(json.dumps(acq['location']))
    return poly

def coverage (aoi, acqs, eofs):
    '''compute the percentage of the coverage

    The acquisitions (acqs) need to be shifted to footprints via the orbit file
    then those footprints unioned and then intersected with the aoi['location'].

    The result is the area(intersection)/area(aoi['location'])*100
    '''
    try:
        fps = unionize ([convert (acq, eof) for acq,eof in zip(acqs,eofs)])
        aoi_ = convert (aoi)
        area = [intersection_area (aoi_, fp) for fp in fps]
        percent = sum(area) / aoi_.Area() * 100.
    except xml.etree.ElementTree.ParseError:
        traceback.print_exc()
        percent = 0
        pass
    print ('->     coverage:',percent)
    return percent

def intersection_area (aoi, fpt):
    '''compute the area of intersection between aoi and fp'''
    intersection = aoi.Intersection (fpt)
    return intersection.Area() if intersection else 0

def project (latlon, to_map='cyl'):
    '''cylindrial projection of lat/lon data'''
    mmap = Basemap(projection=to_map)
    lat,lon = mmap(latlon[:,1], latlon[:,0])
    # Because the projection is serialized by json.dumps() it must be a list
    # and not a zip object. Also, osgeo wants the polygon to be closed meaning
    # the first and last elements of the list need to be the same. For both of
    # these reasons the comprehension is useful despite pylints message.
    # pylint: disable=unnecessary-comprehension
    projection = [ll for ll in zip(lat,lon)] + [(lat[0],lon[0])]
    # pylint: enable=unnecessary-comprehension
    projection.append (projection[0])
    return projection

def prune (aoi, acqs, eofs):
    '''passband filter for acqs and eofs whose footprint intersects the AOI

    Somewhat evily, this routine modifies acqs and eofs inline rather than
    returning the shortened arrays. This was done just to make the code changes
    simpler and keep them localized to a single place namely
    active.enough_coverage().
    '''
    acqs_intersected = []
    aoi_ = convert (aoi)
    aoi_area = aoi_.Area()
    eofs_intersected = []
    for i,fpt in enumerate([convert (acq, eof) for acq,eof in zip(acqs,eofs)]):
        percent = intersection_area (aoi_, fpt) / aoi_area * 100.
        if  percent > 100 - context.coverage_threshold_percent():
            acqs_intersected.append (acqs[i])
            eofs_intersected.append (eofs[i])
            pass
        pass
    acqs.clear()
    acqs.extend (acqs_intersected)
    eofs.clear()
    eofs.extend (eofs_intersected)
    return

def track (acq:{}, eof:{})->[()]:
    '''compute the footprint within an acquisition

    return [(lat,lon)]
    '''
    # generating an Sentinel-1 burst dummy file populated with state vector
    # information for the requested time-period
    burst = orbit.extract (acq['starttime'], acq['endtime'], orbit.load (eof))
    # Sentinel constants
    near_range = 800e3  # Near range in m
    far_range = 950e3   # Far range in m
    doppler = 0        # zero doppler
    wvl = 0.056        # wavelength

    # sampling the ground swath (near and far range) in 10 samples
    cur = datetime.datetime.fromisoformat (acq['starttime'][:-1])
    end = datetime.datetime.fromisoformat (acq['endtime'][:-1])
    coord = numpy.empty ((int((end-cur).total_seconds())*2+2, 3),
                         dtype=numpy.double)
    for i in range(coord.shape[0]//2):
        coord[i][:] = topo (burst, cur, near_range, doppler, wvl)
        coord[coord.shape[0]-i-1][:] = topo(burst, cur, far_range, doppler, wvl)
        cur = cur + datetime.timedelta(seconds=1)
        pass
    return project (coord)

def topo (burst:BurstSLC, time, span, doppler=0, wvl=0.056):
    '''Compute Lat/Lon from inputs'''
    # Provide a zero doppler polygon in case 0 is given
    if doppler == 0:
        doppler = Poly2D()
        doppler.initPoly(rangeOrder=1, azimuthOrder=0, coeffs=[[0, 0]])
        pass

    # compute the lonlat grid
    latlon = burst.orbit.rdr2geo (time, span, doppler=doppler, wvl=wvl)
    return latlon

def unionize (polys):
    '''Create the union of a list of shapely polygons'''
    independent = [True for poly in polys]
    unions = []
    for i,poly in enumerate(polys):
        for j,union in enumerate(unions):
            active_union = union.Union (poly)

            if active_union:
                independent[i] = False
                unions[j] = active_union
                break
        else: unions.append (poly)  # for/else construct
        pass

    if not all(independent): unions = unionize (unions)
    return unions
