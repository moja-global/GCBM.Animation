class Colorizer:
    '''
    Creates a legend and color scheme for a collection of layers.
    '''

    def create_legend(self, layers, palette="hls"):
        '''
        Creates a legend and color scheme for the specified group of layers.

        Arguments:
        'layers' -- list of Layer objects to create a legend and color scheme for.
        'palette' -- the color palette to use. Can be the name of any seaborn palette
            (deep, muted, bright, pastel, dark, colorblind, hls, husl) or matplotlib
            colormap. To find matplotlib colormaps:
            from matplotlib import cm; dir(cm)
        '''
        raise NotImplementedError()

    def _format_value(self, value):
        return f"{value:.2f}" if isinstance(value, float) else f"{value}"
