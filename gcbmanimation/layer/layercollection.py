import os
import gdal
import seaborn as sns
from itertools import chain
from collections import defaultdict
from gcbmanimation.layer.layer import Layer
from gcbmanimation.layer.units import Units
from gcbmanimation.layer.layer import BlendMode
from gcbmanimation.animator.frame import Frame
from gcbmanimation.util.tempfile import TempFileManager

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
    'background_color' -- RGB tuple for the background color.
    '''

    def __init__(self, layers=None, palette="hls", background_color=(224, 224, 224)):
        self._layers = layers or []
        self._palette = palette
        self._background_color = background_color

    @property
    def empty(self):
        '''Checks if this collection is empty.'''
        return not self._layers

    @property
    def layers(self):
        '''Gets the layers in this collection.'''
        return list(self._layers)

    def append(self, layer):
        '''Appends a layer to the collection.'''
        self._layers.append(layer)

    def merge(self, other):
        '''Merges another LayerCollection's layers into this one.'''
        self._layers.extend(other._layers)

    def blend(self, other, method=BlendMode.Add):
        '''Blends the layers in this collection with the layers in another.'''
        blended_collection = LayerCollection(palette=self._palette, background_color=self._background_color)
        years = set(chain((layer.year for layer in self._layers), (layer.year for layer in other._layers)))
        for year in years:
            local_layers = list(filter(lambda layer: layer.year == year, self._layers))
            other_layers = list(filter(lambda layer: layer.year == year, other._layers))
            if len(local_layers) > 1 or len(other_layers) > 1:
                raise RuntimeError("Cannot blend collections containing more than one layer per year.")

            if local_layers:
                local_layer = local_layers[0]
            else:
                placeholder = self._layers[0].flatten(0) if self._layers else other._layers[0].flatten(0)
                local_layer = Layer(placeholder.path, year, placeholder.interpretation)
                    
            if other_layers:
                other_layer = other_layers[0]
            else:
                placeholder = local_layer.flatten(0)
                other_layer = Layer(placeholder.path, year, placeholder.interpretation)

            blended_layer = local_layer.blend(other_layer, method)
            blended_collection.append(blended_layer)

        return blended_collection

    def render(self, bounding_box=None, start_year=None, end_year=None, units=Units.TcPerHa):
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
        'units' -- optional units to render the output in (default: tc/ha). Layers
            in the collection will be converted to these units if necessary.
        
        Returns a list of rendered Frame objects and a legend (dict) describing
        the colors.
        '''
        layer_years = {layer.year for layer in self._layers}
        render_years = set(range(start_year, end_year + 1)) if start_year and end_year else layer_years
        working_layers = [layer for layer in self._layers if layer.year in render_years]
        if bounding_box:
            working_layers = [bounding_box.crop(layer) for layer in working_layers]

        working_layers = [layer.convert_units(units) for layer in working_layers]

        common_interpretation = None
        interpreted = any((layer.has_interpretation for layer in working_layers))
        if interpreted:
            # Interpreted layers where the pixel values have meaning, i.e. a disturbance type,
            # get their pixel values normalized across the whole collection.
            unique_values = sorted(set(chain(*(layer.interpretation.values() for layer in working_layers))))
            common_interpretation = {i: value for i, value in enumerate(unique_values, 1)}
            working_layers = [layer.reclassify(common_interpretation) for layer in working_layers]

        # Merge the layers together by year if this is a fragmented collection of layers,
        # i.e. fire and harvest in separate files.
        layers_by_year = defaultdict(list)
        for layer in working_layers:
            layers_by_year[layer.year].append(layer)

        background_layer = bounding_box or working_layers[0]
        background_frame = background_layer.flatten().render(
            {1: {"color": self._background_color}}, bounding_box=bounding_box, transparent=False)

        working_layers = [self._merge_layers(layers) for layers in layers_by_year.values()]
        legend = self._create_legend(working_layers, common_interpretation)
        rendered_layers = [
            layer.render(legend).composite(background_frame, send_to_bottom=True)
            for layer in working_layers]

        missing_years = render_years - layer_years
        rendered_layers.extend([
            Frame(year, background_frame.path, background_frame.scale)
            for year in missing_years])
        
        return rendered_layers, legend

    def _merge_layers(self, layers):
        output_path = TempFileManager.mktmp(suffix=".tif")
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
                        "label": f"<= {self._format_value(value)}",
                        "color": next(rgb_colors)}
                elif i + 1 == bins:
                    value = max_value - bin_size
                    legend[value] = {
                        "label": f"> {self._format_value(value)}",
                        "color": next(rgb_colors)}
                else:
                    range_min = min_value + i * bin_size
                    range_max = min_value + (i + 1) * bin_size
                    legend[(range_min, range_max)] = {
                        "label": f"{self._format_value(range_min)} to {self._format_value(range_max)}",
                        "color": next(rgb_colors)}
       
        return legend

    def _format_value(self, value):
        return f"{value:.2f}" if isinstance(value, float) else f"{value}"
