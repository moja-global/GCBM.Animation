from util.tempfile import mktmp
from animator.frame import Frame
from matplotlib import pyplot as plt

class Legend:

    def __init__(self, legends):
        self._legends = legends

    def render(self):
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

            out_file = mktmp(suffix=".png")
            fig_legend.savefig(out_file, bbox_inches="tight")
            frames.append(Frame(0, out_file))

        first_frame = frames[0]
        legend_frame = first_frame.merge_horizontal(*frames[1:])

        return legend_frame
