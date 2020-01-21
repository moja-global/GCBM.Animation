import seaborn as sns
from gcbmanimation.layer.colorizer import Colorizer

class SimpleColorizer(Colorizer):
    '''
    Simple colorizer - creates a legend using 8 equal-sized bins.
    '''

    def create_legend(self, layers, palette="hls"):
        bins = 8
        min_value = min((layer.min_max[0] for layer in layers)) - 0.5
        max_value = max((layer.min_max[1] for layer in layers)) + 0.5
        bin_size = (max_value - min_value) / bins
            
        rgb_pct_colors = sns.color_palette(palette, bins)
        rgb_colors = ((int(r_pct * 255), int(g_pct * 255), int(b_pct * 255))
                        for r_pct, g_pct, b_pct in rgb_pct_colors)

        legend = {}
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
