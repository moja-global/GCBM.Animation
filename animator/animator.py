import os
import imageio
from animator.layout.quadrantlayout import QuadrantLayout
from animator.legend import Legend

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

    def render(self, bounding_box=None, start_year=None, end_year=None):
        layout = QuadrantLayout((50, 60), (50, 60), (50, 40), (50, 40))
        disturbance_frames, disturbance_legend = self._disturbances.render(bounding_box, start_year, end_year)
        for indicator in self._indicators:
            graph_frames = indicator.render_graph_frames()
            indicator_frames, indicator_legend = indicator.render_map_frames(bounding_box)
            indicator_legend_title = f"{indicator.title} ({indicator.map_units.value[1]})"
            legend_frame = Legend({
                indicator_legend_title: indicator_legend,
                "Disturbances": disturbance_legend
            }).render()

            animation_frames = []
            for year in range(start_year, end_year + 1):
                disturbance_frame = self._find_frame(disturbance_frames, year)
                indicator_frame = self._find_frame(indicator_frames, year)
                graph_frame = self._find_frame(graph_frames, year)
                title = f"{indicator.title}, Year: {year}"
                animation_frames.append(layout.render(
                    disturbance_frame, indicator_frame, graph_frame, legend_frame,
                    "Disturbances", indicator_legend_title, indicator.title,
                    title=title, dimensions=(3840, 2160)))

            video_frames = [imageio.imread(frame.path) for frame in animation_frames]
            video_frames.append(video_frames[-1]) # Duplicate the last frame to display longer.

            imageio.mimsave(os.path.join(self._output_path, f"{indicator.title}.wmv"), video_frames, fps=1)

    def _find_frame(self, frame_collection, year, default=None):
        return next(filter(lambda frame: frame.year == year, frame_collection), None)
