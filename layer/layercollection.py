import os
import gdal
import seaborn as sns
from itertools import chain
from collections import defaultdict
from layer.layer import Layer
from animator.frame import Frame
from util.tempfile import mktmp

class LayerCollection:
    '''
    A collection of :class:`Layer`s that belong together in an animation.
    '''

    def __init__(self, layers=None, palette="hls"):
        self._layers = layers or []
        self._palette = palette

    @property
    def empty(self):
        return not self._layers

    def append(self, layer):
        self._layers.append(layer)

    def render(self, bounding_box=None, start_year=None, end_year=None):
        layer_years = {layer.year for layer in self._layers}
        render_years = set(range(start_year, end_year + 1)) if start_year and end_year else layer_years
        working_layers = [layer for layer in self._layers if layer.year in render_years]

        common_interpretation = None
        interpreted = any((layer.has_interpretation for layer in working_layers))
        if interpreted:
            # Interpreted layers where the pixel values have meaning, i.e. a disturbance type,
            # get their pixel values normalized across the whole collection.
            unique_values = set(chain(*(layer.interpretation.values() for layer in working_layers)))
            common_interpretation = {i: value for i, value in enumerate(unique_values, 1)}
            working_layers = [layer.reclassify(common_interpretation) for layer in working_layers]

        # Merge the layers together by year if this is a fragmented collection of layers,
        # i.e. fire and harvest in separate files.
        layers_by_year = defaultdict(list)
        for layer in working_layers:
            if layer.year in render_years:
                layers_by_year[layer.year].append(layer)

        background_layer = bounding_box or working_layers[0]
        background_frame = background_layer.flatten().render(
            {1: {"color": (128, 128, 128)}}, bounding_box, transparent=False)

        working_layers = [self._merge(layers) for layers in layers_by_year.values()]
        legend = self._create_legend(working_layers, common_interpretation)
        rendered_layers = [
            layer.render(legend, bounding_box).composite(background_frame, send_to_bottom=True)
            for layer in working_layers]

        missing_years = render_years - layer_years
        rendered_layers.extend([Frame(year, background_frame.path) for year in missing_years])
        
        return rendered_layers, legend

    def _merge(self, layers):
        output_path = mktmp(suffix=".tif")
        gdal.Warp(output_path,
                  [layer.path for layer in layers],
                  multithread=False,
                  creationOptions=["COMPRESS=DEFLATE", "BIGTIFF=YES"])
        
        merged_layer = Layer(output_path, layers[0].year, layers[0].interpretation)

        return merged_layer

    def _create_legend(self, layers, interpretation=None):
        legend = {}

        if interpretation:
            rgb_pct_colors = sns.color_palette(self._palette, len(interpretation))
            rgb_colors = ((int(r_pct * 255), int(g_pct * 255), int(b_pct * 255))
                          for r_pct, g_pct, b_pct in rgb_pct_colors)

            for pixel_value, interpreted_value in interpretation.items():
                legend[pixel_value] = {
                    "label": interpreted_value,
                    "color": next(rgb_colors)}
        else:
            bins = 8
            min_value = min((layer.min_max[0] for layer in layers)) - 0.5
            max_value = max((layer.min_max[1] for layer in layers)) + 0.5
            bin_size = (max_value - min_value) / bins
            
            rgb_pct_colors = sns.color_palette(self._palette, bins)
            rgb_colors = ((int(r_pct * 255), int(g_pct * 255), int(b_pct * 255))
                          for r_pct, g_pct, b_pct in rgb_pct_colors)

            for i in range(bins):
                if i == 0:
                    legend[min_value] = {
                        "label": f"<= {min_value}",
                        "color": next(rgb_colors)}
                elif i + 1 == bins:
                    legend[max_value] = {
                        "label": f"> {max_value}",
                        "color": next(rgb_colors)}
                else:
                    range_min = (i - 1) * bin_size
                    range_max = i * bin_size
                    legend[(range_min, range_max)] = {
                        "label": f"{range_min} to {range_max}",
                        "color": next(rgb_colors)}
       
        return legend
