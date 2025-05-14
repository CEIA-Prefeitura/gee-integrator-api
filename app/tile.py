import math

import pygeohash as pgh

import geopandas as gpd

from shapely.geometry import Point

_base32 = '0123456789bcdefghjkmnpqrstuvwxyz'
_base32_map = {}
for i in range(len(_base32)):
	_base32_map[_base32[i]] = i
del i


def latlon_to_tile(lat, lon, zoom):
    """Converts latitude and longitude to tile coordinates."""
    lat_rad = math.radians(lat)
    n = 2**zoom
    x_tile = int((lon + 180.0) / 360.0 * n)
    y_tile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x_tile, y_tile


def get_brazil_tile_bounds(zoom):
    """Returns the tile boundaries for Brazil at a specific zoom level."""
    # Aproximated boundaries for Brazil
    lat_min, lon_min = -33.7, -73.9  # Southernmost point
    lat_max, lon_max = 5.3, -34.8  # Northernmost point

    x_min, y_min = latlon_to_tile(lat_min, lon_min, zoom)
    x_max, y_max = latlon_to_tile(lat_max, lon_max, zoom)

    return x_min, y_min, x_max, y_max


def is_within_brazil(x, y, z):
    """Check if tile x, y at zoom level z is within the bounds of Brazil."""
    x_min, y_min, x_max, y_max = get_brazil_tile_bounds(z)
    return x in range(x_min, x_max + 1) and y in range(y_max, y_min + 1)


def get_tile_bounds(lat, lon, zoom):
    """Returns the tile boundaries for Brazil at a specific zoom level."""
    # Aproximated boundaries for Brazil
    gdf = gpd.GeoDataFrame(
        [
            {
                "geometry": Point(lon, lat),
            }
        ],
        crs="EPSG:4326",
        geometry="geometry",
    )
    lon_min, lat_min, lon_max, lat_max = (
        gdf.to_crs(3857).geometry.buffer(3000).to_crs(4326).total_bounds
    )

    x_min, y_min = latlon_to_tile(lat_min, lon_min, zoom)
    x_max, y_max = latlon_to_tile(lat_max, lon_max, zoom)

    return x_min, y_min, x_max, y_max


def is_within_boundsbox(lat, lon, x, y, z):
    """Check if tile x, y at zoom level z is within the bounds of Brazil."""
    x_min, y_min, x_max, y_max = get_tile_bounds(lat, lon, z)
    return x in range(x_min, x_max + 1) and y in range(y_max, y_min + 1)


def _int_to_float_hex(i, l):
    if l == 0:
        return -1.0

    half = 1 << (l - 1)
    s = int((l + 3) / 4)
    if i >= half:
        i = i - half
        return float.fromhex(("0x0.%0" + str(s) + "xp1") % (i << (s * 4 - l),))
    else:
        i = half - i
        return float.fromhex(("-0x0.%0" + str(s) + "xp1") % (i << (s * 4 - l),))


def _encode_i2c(lat, lon, lat_length, lon_length):
    precision = int((lat_length + lon_length) / 5)
    if lat_length < lon_length:
        a = lon
        b = lat
    else:
        a = lat
        b = lon

    boost = (0, 1, 4, 5, 16, 17, 20, 21)
    ret = ''
    for i in range(precision):
        ret += _base32[(boost[a & 7] + (boost[b & 3] << 1)) & 0x1F]
        t = a >> 3
        a = b >> 2
        b = t

    return ret[::-1]

def _decode_c2i(hashcode):
    lon = 0
    lat = 0
    bit_length = 0
    lat_length = 0
    lon_length = 0
    for i in hashcode:
        t = _base32_map[i]
        if bit_length % 2 == 0:
            lon = lon << 3
            lat = lat << 2
            lon += (t >> 2) & 4
            lat += (t >> 2) & 2
            lon += (t >> 1) & 2
            lat += (t >> 1) & 1
            lon += t & 1
            lon_length += 3
            lat_length += 2
        else:
            lon = lon << 2
            lat = lat << 3
            lat += (t >> 2) & 4
            lon += (t >> 2) & 2
            lat += (t >> 1) & 2
            lon += (t >> 1) & 1
            lat += t & 1
            lon_length += 2
            lat_length += 3

        bit_length += 5

    return (lat, lon, lat_length, lon_length)

def to_bbox(hashcode):
    '''
    decode a hashcode and get north, south, east and west border.
    '''

    (lat, lon, lat_length, lon_length) = _decode_c2i(hashcode)
    if hasattr(float, "fromhex"):
        latitude_delta = 180.0 / (1 << lat_length)
        longitude_delta = 360.0 / (1 << lon_length)
        latitude = _int_to_float_hex(lat, lat_length) * 90.0
        longitude = _int_to_float_hex(lon, lon_length) * 180.0
        return {"s": latitude, "w": longitude, "n": latitude + latitude_delta, "e": longitude + longitude_delta}

    ret = {}
    if lat_length:
        ret['n'] = 180.0 * (lat + 1 - (1 << (lat_length - 1))) / (1 << lat_length)
        ret['s'] = 180.0 * (lat - (1 << (lat_length - 1))) / (1 << lat_length)
    else:  # can't calculate the half with bit shifts (negative shift)
        ret['n'] = 90.0
        ret['s'] = -90.0

    if lon_length:
        ret['e'] = 360.0 * (lon + 1 - (1 << (lon_length - 1))) / (1 << lon_length)
        ret['w'] = 360.0 * (lon - (1 << (lon_length - 1))) / (1 << lon_length)
    else:  # can't calculate the half with bit shifts (negative shift)
        ret['e'] = 180.0
        ret['w'] = -180.0

    return ret

def tile2goehashBBOX(x_tile, y_tile, zoom):
    """Converts tile coordinates to latitude and longitude."""
    n = 2.0**zoom
    lon = x_tile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / n)))
    lat = math.degrees(lat_rad)
    _hash = pgh.encode(lat, lon, precision=3)
    bbox = to_bbox(_hash)

    return _hash, bbox
