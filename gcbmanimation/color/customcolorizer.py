import seaborn as sns
from gcbmanimation.color.colorizer import Colorizer

class CustomColorizer(Colorizer):
    '''
    Colorizes a set of layers based on a user-provided color scheme. Accepts the
    standard Colorizer constructor arguments plus some CustomColorizer-specific
    settings.

    Arguments:
    'custom_colors' -- a dictionary of tuples of interpreted value to the name of
        a color palette to group the interpreted values by.
    'value_colorizer' -- optional alternative colorizer to use for creating legend
        for layers with no interpretation; if not provided, uses the default method.
    '''

    def __init__(self, custom_colors, value_colorizer=None, **kwargs):
        super().__init__(**kwargs)
        self._value_colorizer = value_colorizer
        self._custom_colors = custom_colors

    def _create_value_legend(self, layers):
        if self._value_colorizer:
            return self._value_colorizer.create_legend(layers)

        return super()._create_value_legend(layers)

    def _create_interpreted_legend(self, layers, interpretation):
        color_map = {}
        for interpreted_values, palette in self._custom_colors.items():
            colors = self._create_colors(palette, len(interpreted_values))
            for value in interpreted_values:
                color_map[value] = next(colors)

        uncustomized_values = set(interpretation.values()) - set(color_map.keys())
        if uncustomized_values:
            colors = self._create_colors(self._palette, len(uncustomized_values))
            for value in uncustomized_values:
                color_map[value] = next(colors)

        legend = {}
        for pixel_value, interpreted_value in interpretation.items():
            legend[pixel_value] = {
                "label": interpreted_value,
                "color": color_map[interpreted_value]}

        return legend
