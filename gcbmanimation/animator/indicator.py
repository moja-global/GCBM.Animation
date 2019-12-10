import os
import numpy as np
from glob import glob
from PIL import Image
from enum import Enum
from contextlib import contextmanager
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
from matplotlib import gridspec
from gcbmanimation.layer.layer import Layer
from gcbmanimation.layer.layercollection import LayerCollection
from gcbmanimation.util.tempfile import TempFileManager
from gcbmanimation.animator.frame import Frame
Image.MAX_IMAGE_PIXELS = None

class Units(Enum):
    
    Blank    = 1,   ""
    Tc       = 1,   "tC/yr"
    Ktc      = 1e3, "KtC/yr"
    Mtc      = 1e6, "MtC/yr"
    TcPerHa  = 1,   "tC/ha/yr"
    KtcPerHa = 1e3, "KtC/ha/yr"
    MtcPerHa = 1e6, "MtC/ha/yr"

class Indicator:
    '''
    Defines an ecosystem indicator from the GCBM results to render into colorized
    Frame objects. An indicator is a collection of spatial outputs and a related
    indicator from the GCBM results database.

    Arguments:
    'results_database' -- a GcbmResultsDatabase for retrieving the non-spatial
        GCBM results.
    'database_indiator' -- the name of an indicator to retrieve from the results
        database.
    'layer_pattern' -- a file pattern (including directory path) in glob format to
        find the spatial outputs for the indicator, i.e. "c:\\my_run\\NPP_*.tif".
    'title' -- the indicator title for presentation - uses the database_indicator
        name if not provided.
    'graph_units' -- a Units enum value for the graph units - result values will
        be divided by this amount.
    'map_units' -- a Units enum value for the map units - spatial output values
        will not be modified, but it is important for this to match the spatial
        output units for the correct unit labels to be displayed in the rendered
        Frames.
    'palette' -- the color palette to use for the rendered map frames - can be the
        name of any seaborn palette (deep, muted, bright, pastel, dark, colorblind,
        hls, husl) or matplotlib colormap. To find matplotlib colormaps:
        from matplotlib import cm; dir(cm)
    '''

    def __init__(self, results_database, database_indicator, layer_pattern,
                 title=None, graph_units=Units.Tc, map_units=Units.TcPerHa,
                 palette="Greens"):
        self._results_database = results_database
        self._database_indicator = database_indicator
        self._layer_pattern = layer_pattern
        self._title = title or database_indicator
        self._graph_units = graph_units or Units.Tc
        self._map_units = map_units or Units.TcPerHa
        self._palette = palette or "Greens"

    @property
    def title(self):
        '''Gets the indicator title.'''
        return self._title

    @property
    def map_units(self):
        '''Gets the Units for the spatial output.'''
        return self._map_units
    
    @property
    def graph_units(self):
        '''Gets the Units for the graphed/non-spatial output.'''
        return self._graph_units
    
    def render_map_frames(self, bounding_box=None):
        '''
        Renders the indicator's spatial output into colorized Frame objects.

        Arguments:
        'bounding_box' -- optional bounding box Layer; spatial output will be
            cropped to the bounding box's minimum spatial extent and nodata pixels.

        Returns a list of colorized Frames, one for each year of output, and a
        legend in dictionary format describing the colors.
        '''
        start_year, end_year = self._results_database.simulation_years
        layers = self._find_layers()
        
        return layers.render(bounding_box, start_year, end_year)

    def render_graph_frames(self):
        '''
        Renders the indidator's non-spatial output into Frame objects. Returns a
        list of Frames, one for each year of output.
        '''
        units, units_label = self._graph_units.value
        indicator_data = self._results_database.get_annual_result(self._database_indicator, units)

        years = list(indicator_data.keys())
        values = list(indicator_data.values())

        frames = []
        for i, year in enumerate(years):
            with self._figure(figsize=(10, 5)) as fig:
                y_label = f"{self._title} ({units_label})"
                plt.xlabel("Years", fontweight="bold", fontsize=14)
                plt.ylabel(y_label, fontweight="bold", fontsize=14)
                plt.axhline(0, color="darkgray")
                plt.plot(years, values, marker="o", linestyle="--", color="navy")
                
                # Mark the current year.
                plt.plot(year, indicator_data[year], marker="o", linestyle="--", color="b", markersize=15)

                plt.axis([None, None, min(values) - 0.1, max(values) + 0.1])
                plt.tick_params(axis="both", labelsize=14)
                plt.xticks(fontsize=12, fontweight="bold")
                plt.yticks(fontsize=12, fontweight="bold")

                # Remove scientific notation.
                ax = plt.gca()
                ax.get_yaxis().get_major_formatter().set_useOffset(False)

                # Add a vertical line at the current year.
                pos = year - 0.2 if i == len(years) - 1 else year + 0.2
                plt.axvspan(year, pos, facecolor="g", alpha=0.5)

                # Shade underneath the value series behind the current year.
                shaded_years = np.array(years)
                shaded_values = np.array(values).copy()
                shaded_values[shaded_years > year] = np.nan
                plt.fill_between(shaded_years, shaded_values, facecolor="gainsboro")

                out_file = TempFileManager.mktmp(suffix=".png")
                fig.savefig(out_file, bbox_inches="tight", dpi=300)
                frames.append(Frame(year, out_file))

        return frames

    @contextmanager
    def _figure(self, *args, **kwargs):
        fig = plt.figure(*args, **kwargs)
        try:
            yield fig
        finally:
            plt.close(fig)
            plt.clf()
       
    def _find_layers(self):
        layers = LayerCollection(palette=self._palette, background_color=(255, 255, 255))
        for layer_path in glob(self._layer_pattern):
            year = os.path.splitext(layer_path)[0][-4:]
            layer = Layer(layer_path, year)
            layers.append(layer)

        if layers.empty:
            raise IOError(f"No spatial output found for pattern: {self._layer_pattern}")

        return layers
