import os
from glob import glob
from gcbmanimation.layer.simplecolorizer import SimpleColorizer
from gcbmanimation.layer.units import Units
from gcbmanimation.layer.layer import Layer
from gcbmanimation.layer.layercollection import LayerCollection
from gcbmanimation.plot.basicresultsplot import BasicResultsPlot

class Indicator:
    '''
    Defines an ecosystem indicator from the GCBM results to render into colorized
    Frame objects. An indicator is a collection of spatial outputs and a related
    indicator from the GCBM results database.

    Arguments:
    'indicator' -- the short name of the indicator.
    'layer_pattern' -- a file pattern (including directory path) in glob format to
        find the spatial outputs for the indicator, i.e. "c:\\my_run\\NPP_*.tif";
        can also be specified as a tuple of (file pattern, Units) to specify the
        native units of the layers (i.e. Units.Tc) - otherwise the default of
        Units.TcPerHa is used.
    'results_provider' -- a GcbmResultsProvider for retrieving the non-spatial
        GCBM results.
    'provider_filter' -- filter to pass to results_provider to retrieve a single
        indicator.
    'title' -- the indicator title for presentation - uses the indicator name if
        not provided.
    'graph_units' -- a Units enum value for the graph units - result values will
        be converted to these units.
    'map_units' -- a Units enum value for the map units - spatial output values
        will be converted to the target units if necessary.
    'palette' -- the color palette to use for the rendered map frames - can be the
        name of any seaborn palette (deep, muted, bright, pastel, dark, colorblind,
        hls, husl) or matplotlib colormap. To find matplotlib colormaps:
        from matplotlib import cm; dir(cm)
    'background_color' -- the background (bounding box) color to use for the map
        frames.
    'map_colorizer' -- a Colorizer to create the map legend with - defaults to
        SimpleColorizer which bins values into 8 equal-sized buckets.
    '''

    def __init__(self, indicator, layer_pattern, results_provider, provider_filter=None,
                 title=None, graph_units=Units.Tc, map_units=Units.TcPerHa, palette="Greens",
                 background_color=(255, 255, 255), map_colorizer=None):
        self._indicator = indicator
        self._layer_pattern = layer_pattern
        self._results_provider = results_provider
        self._provider_filter = provider_filter or {}
        self._title = title or indicator
        self._graph_units = graph_units or Units.Tc
        self._map_units = map_units or Units.TcPerHa
        self._palette = palette or "Greens"
        self._background_color = background_color
        self._map_colorizer = map_colorizer or SimpleColorizer()

    @property
    def title(self):
        '''Gets the indicator title.'''
        return self._title

    @property
    def indicator(self):
        '''Gets the short title for the indicator.'''
        return self._indicator

    @property
    def map_units(self):
        '''Gets the Units for the spatial output.'''
        return self._map_units
    
    @property
    def graph_units(self):
        '''Gets the Units for the graphed/non-spatial output.'''
        return self._graph_units

    @property
    def simulation_years(self):
        '''Gets the years present in the simulation.'''
        return self._results_provider.simulation_years
    
    def render_map_frames(self, bounding_box=None, start_year=None, end_year=None):
        '''
        Renders the indicator's spatial output into colorized Frame objects.

        Arguments:
        'bounding_box' -- optional bounding box Layer; spatial output will be
            cropped to the bounding box's minimum spatial extent and nodata pixels.

        Returns a list of colorized Frames, one for each year of output, and a
        legend in dictionary format describing the colors.
        '''
        layers = self._find_layers()
        if not start_year or not end_year:
            start_year, end_year = self._results_provider.simulation_years
        
        return layers.render(bounding_box, start_year, end_year, self._map_units)

    def render_graph_frames(self, start_year=None, end_year=None, **kwargs):
        '''
        Renders the indicator's non-spatial output into a graph.

        Arguments:
        Any accepted by GCBMResultsProvider and subclasses.

        Returns a list of Frames, one for each year of output.
        '''
        plot = BasicResultsPlot(self._indicator, self._results_provider, self._graph_units)
        
        return plot.render(start_year=start_year, end_year=end_year, **self._provider_filter, **kwargs)
       
    def _find_layers(self):
        pattern = self._layer_pattern
        units = Units.TcPerHa
        if isinstance(self._layer_pattern, tuple):
            pattern, units = self._layer_pattern

        layers = LayerCollection(palette=self._palette,
                                 background_color=self._background_color,
                                 colorizer=self._map_colorizer)

        for layer_path in glob(pattern):
            year = os.path.splitext(layer_path)[0][-4:]
            layer = Layer(layer_path, year, units=units)
            layers.append(layer)

        if layers.empty:
            raise IOError(f"No spatial output found for pattern: {self._layer_pattern}")

        return layers
