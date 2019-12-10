from matplotlib import pyplot as plt
from gcbmanimation.util.tempfile import TempFileManager
from gcbmanimation.animator.frame import Frame

class Legend:
    '''
    Renders a Frame containing a graphical legend from one or more dictionary-
    format color legends generated internally by LayerCollection.

    Arguments:
    'legends' -- the dictionary-format legends to render.
    '''

    def __init__(self, legends):
        self._legends = legends

    def render(self):
        '''
        Returns a Frame containing a graphical legend generated from the contained
        dictionary-format legends.
        '''
        frames = []
        for legend_title, legend in self._legends.items():
            fig = plt.figure()
            fig_legend = plt.figure(dpi=300)
            ax = fig.add_subplot(111)

            lines = [ax.bar(1, 2, color=[col / 255 for col in entry["color"]])
                     for entry in legend.values()]

            fig_legend.legend(lines,
                              [entry["label"] for entry in legend.values()],
                              "upper left",
                              title=legend_title,
                              frameon=False)

            out_file = TempFileManager.mktmp(suffix=".png")
            fig_legend.savefig(out_file, bbox_inches="tight")
            frames.append(Frame(0, out_file))

        first_frame = frames[0]
        legend_frame = first_frame.merge_horizontal(*frames[1:])

        return legend_frame
