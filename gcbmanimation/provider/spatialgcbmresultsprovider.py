import os
import sqlite3
import gdal
from glob import glob
from collections import OrderedDict
from gcbmanimation.layer.layer import Layer
from gcbmanimation.provider.gcbmresultsprovider import GcbmResultsProvider
from gcbmanimation.util.utmzones import find_best_projection

class SpatialGcbmResultsProvider(GcbmResultsProvider):
    '''
    Retrieves non-spatial annual results from a stack of spatial layers.

    Arguments:
    'pattern' -- glob pattern for spatial layers to read.
    'per_hectare' -- whether the values in the spatial layers are absolute or
        per hectare; this must correctly match the layer format in order for the
        annual results to be correct.
    '''

    def __init__(self, pattern, per_hectare=True):
        self._pattern = pattern
        self._per_hectare = per_hectare

    @property
    def simulation_years(self):
        '''See GcbmResultsProvider.simulation_years.'''
        layers = self._find_layers()
        return min((l.year for l in layers)), max((l.year for l in layers))

    def get_annual_result(self, indicator, units=1, bounding_box=None, **kwargs):
        '''See GcbmResultsProvider.get_annual_result.'''
        layers = self._find_layers()

        data = OrderedDict()
        start_year, end_year = self.simulation_years
        for year in range(start_year, end_year + 1):
            layer = self._find_year(layers, year)
            if bounding_box:
                layer = bounding_box.crop(layer)

            value = self._sum_pixels(layer) / units
            data[year] = value

        return data

    def _find_layers(self):
        layers = []
        for layer_path in glob(self._pattern):
            year = os.path.splitext(layer_path)[0][-4:]
            layer = Layer(layer_path, year)
            layers.append(layer)

        if not layers:
            raise IOError(f"No spatial output found for pattern: {self._layer_pattern}")

        return layers

    def _find_year(self, layers, year):
        return next(filter(lambda layer: layer.year == year, layers), None)

    def _sum_pixels(self, layer):
        working_layer = layer
        multiplier = 1
        if self._per_hectare:
            new_projection = find_best_projection(layer)
            working_layer = layer.reproject(new_projection)
            one_hectare = 100 ** 2
            pixel_size_m2 = working_layer.scale ** 2
            multiplier = pixel_size_m2 / one_hectare

        raster = gdal.Open(working_layer.path)
        band = raster.GetRasterBand(1)
        raster_data = band.ReadAsArray()
        raster_data[raster_data == working_layer.nodata_value] = 0
        raster_data = raster_data * multiplier

        return raster_data.sum()
