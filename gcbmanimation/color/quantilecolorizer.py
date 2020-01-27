import gdal
import numpy as np
import seaborn as sns
from pysal.esda.mapclassify import Quantiles
from gcbmanimation.color.colorizer import Colorizer

class QuantileColorizer(Colorizer):
    '''
    Creates a legend using quantiles - usually shows more activity in rendered
    maps than SimpleColorizer.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create_value_legend(self, layers):
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

    def _get_quantile_dataset(self, layers):
        all_layer_data = None
        sample_proportion = 1
        while all_layer_data is None:
            try:
                all_layer_data = np.empty(shape=(0, 0))
                for layer in layers:
                    all_layer_data = np.append(
                        all_layer_data, self._load_layer_data(layer, sample_proportion))
            except MemoryError:
                all_layer_data = None
                sample_proportion = sample_proportion / 2

        return all_layer_data

    def _load_layer_data(self, layer, sample_proportion=1):
        raster = gdal.Open(layer.path)
        raster_data = np.array(raster.GetRasterBand(1).ReadAsArray())
        pixel_count = raster_data.shape[0] * raster_data.shape[1]
        raster_data[np.where(raster_data == layer.nodata_value)] = np.nan
        raster_data = np.reshape(raster_data, pixel_count)
        raster_data = raster_data[np.logical_not(np.isnan(raster_data))]

        if sample_proportion < 1:
            raster_data = np.random.choice(raster_data, int(pixel_count * sample_proportion))
        
        return raster_data
