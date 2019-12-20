import os
import sqlite3
import gdal
from glob import glob
from collections import OrderedDict
from gcbmanimation.layer.layer import Layer
from gcbmanimation.layer.units import Units
from gcbmanimation.provider.gcbmresultsprovider import GcbmResultsProvider
from gcbmanimation.util.utmzones import find_best_projection

class SpatialGcbmResultsProvider(GcbmResultsProvider):
    '''
    Retrieves non-spatial annual results from a stack of spatial layers.

    Arguments:
    'pattern' -- glob pattern for spatial layers to read.
    'layers' -- instead of specifying a file pattern to search for, a list of Layer
        objects can be provided directly.
    '''

    def __init__(self, pattern=None, layers=None):
        self._pattern = pattern
        self._layers = layers
        if not (pattern or layers):
            raise RuntimeError("Must provide either a file pattern or a list of Layer objects")

    @property
    def simulation_years(self):
        '''See GcbmResultsProvider.simulation_years.'''
        layers = self._layers or self._find_layers()
        return min((l.year for l in layers)), max((l.year for l in layers))

    def get_annual_result(self, units=Units.Tc, bounding_box=None, **kwargs):
        '''See GcbmResultsProvider.get_annual_result.'''
        layers = self._layers or self._find_layers()

        data = OrderedDict()
        start_year, end_year = self.simulation_years
        for year in range(start_year, end_year + 1):
            layer = self._find_year(layers, year)
            if bounding_box:
                layer = bounding_box.crop(layer)

            layer = layer.convert_units(units)
            value = self._sum_pixels(layer)
            data[year] = value

        return data

    def _find_layers(self):
        pattern = self._pattern
        units = Units.TcPerHa
        if isinstance(self._pattern, tuple):
            pattern, units = self._pattern

        layers = []
        for layer_path in glob(pattern):
            year = os.path.splitext(layer_path)[0][-4:]
            layer = Layer(layer_path, year, units=units)
            layers.append(layer)

        if not layers:
            raise IOError(f"No spatial output found for pattern: {self._layer_pattern}")

        return layers

    def _find_year(self, layers, year):
        return next(filter(lambda layer: layer.year == year, layers), None)

    def _sum_pixels(self, layer):
        raster = gdal.Open(layer.path)
        band = raster.GetRasterBand(1)
        raster_data = band.ReadAsArray()
        raster_data[raster_data == layer.nodata_value] = 0

        return raster_data.sum()
