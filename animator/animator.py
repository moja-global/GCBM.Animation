class Animator:
    '''
    Creates animations from GCBM results.

    :param disturbances: the 
    :type disturbances: :class:`.LayerCollection`
    '''

    def __init__(self, disturbances, indicators, output_path="."):
        self._disturbances = disturbances
        self._indicators = indicators
        self._output_path = output_path

    def render(start_year, end_year, bounding_box=None):
        disturbance_frames, disturbance_legend = disturbances.render()
        for indicator in self.indicators:
            indicator_frames, indicator_legend = indicator.render_map_frames()
            graph_frames = indicator.render_graph_frames()
            legend_frame = Legend(disturbance_legend, indicator_legend).render()
            for year in range(start_year, end_year + 1):
                disturbance_frame = self._find_frame(disturbance_frames, year)
                indicator_frame = self._find_frame(indicator_frames, year)
                graph_frame = self._find_frame(graph_frames, year)

    def _find_frame(self, frame_collection, year, default=None):
        return next(filter(lambda frame: frame.year == year, frame_collection), None)
