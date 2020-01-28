import gdal
import numpy as np
import seaborn as sns
from enum import Enum
from pysal.esda.mapclassify import Quantiles
from gcbmanimation.color.colorizer import Colorizer

class Filter(Enum):

    Negative = -1
    Positive =  1


class QuantileColorizer(Colorizer):
    '''
    Creates a legend using quantiles - usually shows more activity in rendered
    maps than the standard Colorizer's equal bin size method. Accepts the standard
    Colorizer constructor arguments plus some CustomColorizer-specific settings.

    Arguments:
    'negative_palette' -- optional second color palette name for the value range
        below 0; if provided, value bins are split into above and below zero, with
        positive values using the colors from the 'palette' argument. By default,
        the entire value range (+/-) is binned and colorized together.
    '''

    def __init__(self, negative_palette=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._negative_palette = negative_palette

    def _create_value_legend(self, layers):
        if self._negative_palette:
            return self._create_split_value_legend(layers)
        else:
            return self._create_simple_value_legend(layers)

    def _create_simple_value_legend(self, layers):
        quantile_data = self._get_quantile_dataset(layers)
        quantiles = Quantiles(quantile_data, k=self._bins)
        bins = quantiles.bins
        colors = self._create_colors(self._palette, self._bins)

        legend = {}
        for i, upper_bound in enumerate(bins):
            if i == 0:
                legend[upper_bound] = {
                    "label": f"<= {self._format_value(upper_bound)}",
                    "color": next(colors)}
            else:
                lower_bound = bins[i - 1]
                legend[(lower_bound, upper_bound)] = {
                    "label": f"{self._format_value(lower_bound)} to {self._format_value(upper_bound)}",
                    "color": next(colors)}
       
        return legend

    def _create_split_value_legend(self, layers):
        legend = {}
        k = self._bins // 2

        negative_data = self._get_quantile_dataset(layers, Filter.Negative)
        negative_quantiles = Quantiles(negative_data, k=k)
        negative_bins = negative_quantiles.bins
        negative_colors = list(self._create_colors(self._negative_palette, k))

        for i, upper_bound in enumerate(negative_bins):
            if i == 0:
                legend[upper_bound] = {
                    "label": f"<= {self._format_value(upper_bound)}",
                    "color": negative_colors[-i - 1]}
            else:
                upper_bound = 0 if i == k - 1 else upper_bound
                lower_bound = negative_bins[i - 1]
                legend[(lower_bound, upper_bound)] = {
                    "label": f"{self._format_value(lower_bound)} to {self._format_value(upper_bound)}",
                    "color": negative_colors[-i - 1]}

        positive_data = self._get_quantile_dataset(layers, Filter.Positive)
        positive_quantiles = Quantiles(positive_data, k=k)
        positive_bins = positive_quantiles.bins
        positive_colors = self._create_colors(self._palette, k)

        for i, upper_bound in enumerate(positive_bins):
            lower_bound = 0 if i == 0 else positive_bins[i - 1]
            legend[(lower_bound, upper_bound)] = {
                "label": f"{self._format_value(lower_bound)} to {self._format_value(upper_bound)}",
                "color": next(positive_colors)}

        return legend

    def _get_quantile_dataset(self, layers, filter=None):
        all_layer_data = None
        sample_proportion = 1
        while all_layer_data is None:
            try:
                all_layer_data = np.empty(shape=(0, 0))
                for layer in layers:
                    all_layer_data = np.append(
                        all_layer_data, self._load_layer_data(layer, sample_proportion, filter))
            except MemoryError:
                all_layer_data = None
                sample_proportion = sample_proportion / 2

        return all_layer_data

    def _load_layer_data(self, layer, sample_proportion=1, filter=None):
        raster = gdal.Open(layer.path)
        raster_data = np.array(raster.GetRasterBand(1).ReadAsArray())
        pixel_count = raster_data.shape[0] * raster_data.shape[1]
        raster_data[np.where(raster_data == layer.nodata_value)] = np.nan
        raster_data = np.reshape(raster_data, pixel_count)
        raster_data = raster_data[np.logical_not(np.isnan(raster_data))]

        if filter == Filter.Negative:
            raster_data = raster_data[np.where(raster_data <= 0)]
        elif filter == Filter.Positive:
            raster_data = raster_data[np.where(raster_data > 0)]

        if sample_proportion < 1:
            raster_data = np.random.choice(raster_data, int(pixel_count * sample_proportion))
        
        return raster_data
