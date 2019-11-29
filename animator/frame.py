from PIL import Image
from util.tempfile import mktmp

class Frame:

    def __init__(self, year, path):
        self._year = year
        self._path = path

    @property
    def year(self):
        return self._year

    @property
    def path(self):
        return self._path

    def composite(self, frame, send_to_bottom=False):
        out_path = mktmp(suffix=".png")
        this_image = Image.open(self._path)
        other_image = Image.open(frame.path)

        if send_to_bottom:
            Image.alpha_composite(other_image, this_image).save(out_path)
        else:
            Image.alpha_composite(this_image, other_image).save(out_path)

        return Frame(self._year, out_path)
