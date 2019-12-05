import os
import gdal
import seaborn as sns
from itertools import chain
from collections import defaultdict
from gcbmanimation.layer.layer import Layer
from gcbmanimation.animator.frame import Frame
from gcbmanimation.util.tempfile import mktmp

class LayerCollection:
    '''
    A collection of Layer objects that belong together in an animation. The layers
    in the collection should be generally related, i.e. a collection of interpreted
    layers along the same theme (disturbances), or a collection of value layers for
    the same indicator (NPP, ...).

    Layers in the collection can be for different years - when the collection is
    rendered, the layers will be merged together by year, and each year will
    become a separate Frame object.

    Arguments:
    'layers' -- a list of Layer objects to include in the collection.
    'palette' -- the color palette to use for the rendered frames - can be the
        name of any seaborn palette (deep, muted, bright, pastel, dark, colorblind,
        hls, husl) or matplotlib colormap. To find matplotlib colormaps:
        from matplotlib import cm; dir(cm)
    '''

    def __init__(self, layers=None, palette="hls"):
        self._layers = layers or []
        self._palette = palette

    @property
    def empty(self):
        '''Checks if this collection is empty.'''
        return not self._layers

    def append(self, layer):
        '''Appends a layer to the collection.'''
        self._layers.append(layer)

    def merge(self, other):
        '''Merges another LayerCollection's layers into this one.'''
        self._layers.extend(other._layers)

    def render(self, bounding_box=None, start_year=None, end_year=None):
        '''
        Renders the collection of layers into colorized Frame objects organized
        by year.

        Arguments:
        'bounding_box' -- optional bounding box Layer; rendered layers in this
            collection will be cropped to the bounding box's minimum spatial extent
            and nodata pixels. The bounding box also has its data values flattened
            to grey and becomes the background layer.
        'start_year' -- optional start year to render from - must be specified
            along with end_year.
        'end_year' -- optional end year to render to - must be specified along
            with start_year.
        
        Returns a list of rendered Frame objects and a legend (dict) describing
        the colors.
        '''
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
            layers_by_year[layer.year].append(layer)

        background_layer = bounding_box or working_layers[0]
        background_frame = background_layer.flatten().render(
            {1: {"color": (128, 128, 128)}}, bounding_box, transparent=False)

        working_layers = [self._merge_layers(layers) for layers in layers_by_year.values()]
        legend = self._create_legend(working_layers, common_interpretation)
        rendered_layers = [
            layer.render(legend, bounding_box).composite(background_frame, send_to_bottom=True)
            for layer in working_layers]

        missing_years = render_years - layer_years
        rendered_layers.extend([Frame(year, background_frame.path) for year in missing_years])
        
        return rendered_layers, legend

    def _merge_layers(self, layers):
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
                    value = min_value + bin_size
                    legend[value] = {
                        "label": f"<= {value}",
                        "color": next(rgb_colors)}
                elif i + 1 == bins:
                    value = max_value - bin_size
                    legend[value] = {
                        "label": f"> {value}",
                        "color": next(rgb_colors)}
                else:
                    range_min = min_value + i * bin_size
                    range_max = min_value + (i + 1) * bin_size
                    legend[(range_min, range_max)] = {
                        "label": f"{range_min} to {range_max}",
                        "color": next(rgb_colors)}
       
        return legend
