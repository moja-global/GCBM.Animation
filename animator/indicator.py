import numpy as np
from PIL import Image
from enum import Enum
from contextlib import contextmanager
from matplotlib import image as mpimg
from matplotlib import pyplot as plt
from matplotlib import gridspec
from layer.layercollection import LayerCollection
from util.tempfile import mktmp
from animator.frame import Frame

class Units(Enum):
    
    Default = 1,   "tC/yr"
    Ktc     = 1e3, "KtC/yr"
    Mtc     = 1e6, "MtC/yr"


class Indicator:

    def __init__(self, results_database, database_indicator, layers, title=None, units=Units.Default):
        self._results_database = results_database
        self._database_indicator = database_indicator
        self._layers = layers
        self._title = title or database_indicator
        self._units = units

    @property
    def title(self):
        return self._title
    
    def render_map_frames(self, bounding_box=None):
        start_year, end_year = self._results_database.simulation_years
        
        return self._layers.render(bounding_box, start_year, end_year)

    def render_graph_frames(self, bounding_box=None):
        units, units_label = self._units.value
        indicator_data = self._results_database.get_annual_result(self._database_indicator, units)

        years = list(indicator_data.keys())
        values = list(indicator_data.values())

        frames = []
        for i, year in enumerate(years):
            with self._figure(figsize=(10, 5)) as fig:
                y_label = f"{self._title} ({units_label})"
                plt.xlabel("Years", fontweight="bold")
                plt.ylabel(y_label, fontweight="bold")
                plt.axhline(0, color="darkgray")
                plt.plot(years, values, marker="o", linestyle="--", color="navy")
                
                # Mark the current year.
                plt.plot(year, indicator_data[year], marker="o", linestyle="--", color="b", markersize=15)

                plt.axis([None, None, min(values) - 0.1, max(values) + 0.1])
                plt.tick_params(axis="both", labelsize=12)

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

                out_eps = mktmp(suffix=".eps")
                fig.savefig(out_eps, bbox_inches="tight", dpi=300)
                out_png = self._export_to_png(out_eps)
                frames.append(Frame(year, out_png))

        return frames

    @contextmanager
    def _figure(self, *args, **kwargs):
        fig = plt.figure(*args, **kwargs)
        try:
            yield fig
        finally:
            plt.close(fig)
            plt.clf()
    
    def _export_to_png(self, eps):
        eps_image = Image.open(eps)
        output_path = mktmp(suffix=".png")
        eps_image.load(scale=7)
        eps_image.save(output_path)
        eps_image.close()
       
        return output_path
