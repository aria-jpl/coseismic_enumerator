'''transact with geo-data and satelite data'''

import datetime
import isce  # pylint: disable=unused-import
import json
import numpy
import orbit
import osgeo.ogr

from isceobj.Sensor.TOPS.BurstSLC import BurstSLC
from isceobj.Util.Poly2D import Poly2D
from mpl_toolkits.basemap import Basemap

def convert (acq, eof=None):
    '''convert an object with ['location'] to a shapely polygon'''
    if eof:
        # FIXME: should actually do commented out code
        # location = {'shape':{'ccordinates':track (acq, eof),
        #                     'type':'Polygon'}}
        # poly = osgeo.ogr.CreateGeometryFromJson(json.dumps(location))
        poly = osgeo.ogr.CreateGeometryFromJson(json.dumps(acq['location']))
    else:  poly = osgeo.ogr.CreateGeometryFromJson(json.dumps(acq['location']))
    return poly

def coverage (aoi, acqs, eofs):
    '''compute the percentage of the coverage

    The acquisitions (acqs) need to be shifted to footprints via the orbit file
    then those footprints unioned and then intersected with the aoi['location'].

    The result is the area(intersection)/area(aoi['location'])*100
    '''
    fps = [convert (acq, eof) for acq,eof in zip(acqs,eofs)]
    whole_fp = union (fps)
    aoi_ = convert (aoi)
    intersection = aoi_.Intersection (whole_fp)
    percent = intersection.Area() / aoi_.Area() * 100.
    print ('    coverage:',percent)
    return percent

def project (latlon, to_map='cyl'):
    '''cylindrial projection of lat/lon data'''
    mmap = Basemap(projection=to_map)
    lat,lon = mmap(latlon[:,1], latlon[:,0])
    return zip(lat,lon)

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
    coord = numpy.empty ((int((end-cur).total_seconds())*2+2, 2),
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

def union (polys):
    '''Create the union of a list of shapely polygons'''
    result = polys[0]
    for poly in polys[1:]: result = result.Union (poly)
    return result
