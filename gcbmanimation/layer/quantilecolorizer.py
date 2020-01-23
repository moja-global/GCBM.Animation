import gdal
import numpy as np
import seaborn as sns
from pysal.esda.mapclassify import Quantiles
from gcbmanimation.layer.colorizer import Colorizer

class QuantileColorizer(Colorizer):
    '''
    Creates a legend using quantiles - usually shows more activity in rendered
    maps than SimpleColorizer.
    '''

    def __init__(self, bins=8):
        self._bins = bins

    def create_legend(self, layers, palette="hls"):
        all_layer_data = np.empty(shape=(0, 0))
        for layer in layers:
            all_layer_data = np.append(all_layer_data, self._load_layer_data(layer))

        quantiles = Quantiles(all_layer_data, k=self._bins)
        bins = quantiles.bins

        rgb_pct_colors = sns.color_palette(palette, self._bins)
        rgb_colors = ((int(r_pct * 255), int(g_pct * 255), int(b_pct * 255))
                      for r_pct, g_pct, b_pct in rgb_pct_colors)

        legend = {}
        for i, upper_bound in enumerate(bins):
            if i == 0:
                legend[upper_bound] = {
                    "label": f"<= {self._format_value(upper_bound)}",
                    "color": next(rgb_colors)}
            else:
                lower_bound = bins[i - 1]
                legend[(lower_bound, upper_bound)] = {
                    "label": f"{self._format_value(lower_bound)} to {self._format_value(upper_bound)}",
                    "color": next(rgb_colors)}
       
        return legend

    def _load_layer_data(self, layer):
        raster = gdal.Open(layer.path)
        raster_data = np.array(raster.GetRasterBand(1).ReadAsArray())
        pixel_count = raster_data.shape[0] * raster_data.shape[1]
        raster_data[np.where(raster_data == layer.nodata_value)] = np.nan
        raster_data = np.reshape(raster_data, pixel_count)
        raster_data = raster_data[np.logical_not(np.isnan(raster_data))]
        
        return raster_data
