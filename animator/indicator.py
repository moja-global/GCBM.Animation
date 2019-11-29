from layer.layercollection import LayerCollection

class Indicator:

    def __init__(self, result_database, database_indicator, result_layers, title=None):
        self._result_database = result_database
        self._database_indicator = database_indicator
        self._result_layers = result_layers
        self._title = title or database_indicator
        self._start_year = None
        self._end_year = None
    
    def render_map_frames(self, start_year, end_year):
        return self._result_layers.render()

    def render_graph_frames(self, start_year, end_year):
        raise NotImplementedError()
