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

    def merge_horizontal(self, *frames):
        images = [Image.open(self._path)] + [Image.open(frame.path) for frame in frames]
        widths, heights = zip(*(image.size for image in images))

        total_width = sum(widths)
        max_height = max(heights)

        merged_image = Image.new("RGBA", (total_width, max_height), color=(255, 255, 255, 255))

        x_offset = 0
        for image in images:
            merged_image.paste(image, (x_offset, 0))
            x_offset += image.size[0]

        out_path = mktmp(suffix=".png")
        merged_image.save(out_path)

        return Frame(self._year, out_path)
