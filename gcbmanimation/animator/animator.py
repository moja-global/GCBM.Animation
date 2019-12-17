import os
import imageio
from gcbmanimation.animator.layout.quadrantlayout import QuadrantLayout
from gcbmanimation.animator.legend import Legend
from gcbmanimation.util.tempfile import TempFileManager

class Animator:
    '''
    Creates animations from GCBM results. Takes a collection of disturbance layers
    and one or more indicators and produces a WMV for each indicator showing the
    timeseries of disturbances, spatial output, and graphed database output.

    Arguments:
    'disturbances' -- a LayerCollection of the input disturbance layers for the
        GCBM simulation.
    'indicators' -- a list of Indicator objects grouping a set of GCBM spatial
        outputs and a related ecosystem indicator from the GCBM results database.
    'output_path' -- the directory to generate the output video files in.
    '''

    def __init__(self, disturbances, indicators, output_path="."):
        self._disturbances = disturbances
        self._indicators = indicators
        self._output_path = output_path

    def render(self, bounding_box=None, start_year=None, end_year=None):
        '''
        Renders a set of animations, one for each Indicator in this animator.

        Arguments:
        'bounding_box' -- a Layer object to act as a bounding box for the rendered
            frames: disturbance and spatial output layers will be cropped to the
            bounding box's minimum spatial extent and nodata pixels.
        'start_year' -- the year to render from - if not provided, will be detected
            from the indicator.
        'end_year' -- the year to render to - if not provided, will be detected
            from the indicator.
        '''
        layout = QuadrantLayout((50, 60), (50, 60), (50, 40), (50, 40))
        disturbance_frames = None
        disturbance_legend = None
        for indicator in self._indicators:
            graph_frames = indicator.render_graph_frames(bounding_box=bounding_box)
            indicator_frames, indicator_legend = indicator.render_map_frames(bounding_box)

            if not start_year or not end_year:
                start_year = min((frame.year for frame in graph_frames))
                end_year = max((frame.year for frame in graph_frames))

            if not disturbance_frames:
                disturbance_frames, disturbance_legend = self._disturbances.render(
                    bounding_box, start_year, end_year)

            indicator_legend_title = f"{indicator.title} ({indicator.map_units.value[1]})"
            legend_frame = Legend({
                "Disturbances": disturbance_legend,
                indicator_legend_title: indicator_legend
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
            TempFileManager.cleanup("*.tif")

    def _find_frame(self, frame_collection, year, default=None):
        return next(filter(lambda frame: frame.year == year, frame_collection), None)
