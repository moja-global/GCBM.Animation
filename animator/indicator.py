import os
import numpy as np
from glob import glob
from PIL import Image
from enum import Enum
from contextlib import contextmanager
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
from matplotlib import gridspec
from layer.layer import Layer
from layer.layercollection import LayerCollection
from util.tempfile import mktmp
from animator.frame import Frame

class Units(Enum):
    
    Blank    = 1,   ""
    Tc       = 1,   "tC/yr"
    Ktc      = 1e3, "KtC/yr"
    Mtc      = 1e6, "MtC/yr"
    TcPerHa  = 1,   "tC/ha/yr"
    KtcPerHa = 1e3, "KtC/ha/yr"
    MtcPerHa = 1e6, "MtC/ha/yr"

class Indicator:

    def __init__(self, results_database, database_indicator, layer_pattern,
                 title=None, units=Units.Tc, palette="Greens"):
        self._results_database = results_database
        self._database_indicator = database_indicator
        self._layer_pattern = layer_pattern
        self._title = title or database_indicator
        self._units = units
        self._palette = palette

    @property
    def title(self):
        return self._title

    @property
    def units(self):
        return self._units
    
    def render_map_frames(self, bounding_box=None):
        start_year, end_year = self._results_database.simulation_years
        layers = self._find_layers()
        
        return layers.render(bounding_box, start_year, end_year)

    def render_graph_frames(self):
        units, units_label = self._units.value
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

                out_file = mktmp(suffix=".png")
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
        layers = LayerCollection(palette=self._palette)
        for layer_path in glob(self._layer_pattern):
            year = os.path.splitext(layer_path)[0][-4:]
            layer = Layer(layer_path, year)
            layers.append(layer)

        if layers.empty:
            raise IOError(f"No spatial output found for pattern: {self._layer_pattern}")

        return layers
