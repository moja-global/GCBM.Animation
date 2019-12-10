from PIL import Image
from gcbmanimation.util.tempfile import TempFileManager
Image.MAX_IMAGE_PIXELS = None

class Frame:
    '''
    Represents a presentation-format image that can be included in an animation.
    A frame usually applies to a particular year and points to an image file on disk.

    Arguments:
    'year' -- the year this Frame applies to.
    'path' -- the path to the image file this Frame represents.
    '''

    def __init__(self, year, path):
        self._year = year
        self._path = path

    @property
    def year(self):
        '''The year this Frame applies to.'''
        return self._year

    @property
    def path(self):
        '''The path to the Frame's image file.'''
        return self._path

    def composite(self, frame, send_to_bottom=False):
        '''
        Combines another RGBA Frame with this one using their alpha channels.

        Arguments:
        'frame' -- the frame to combine with this one.
        'send_to_bottom' -- use the other frame as the background instead of
            this one.

        Returns the merged image as a new Frame with the same year as this one.
        '''
        out_path = TempFileManager.mktmp(suffix=".png")
        this_image = Image.open(self._path)
        other_image = Image.open(frame.path)

        if send_to_bottom:
            Image.alpha_composite(other_image, this_image).save(out_path)
        else:
            Image.alpha_composite(this_image, other_image).save(out_path)

        return Frame(self._year, out_path)

    def merge_horizontal(self, *frames):
        '''
        Merges one or more Frames horizontally with this one.

        Arguments:
        'frames' -- one or more Frames to merge horizontally.

        Returns the merged image as a new Frame with the same year as this one.
        '''
        images = [Image.open(self._path)] + [Image.open(frame.path) for frame in frames]
        widths, heights = zip(*(image.size for image in images))

        total_width = sum(widths)
        max_height = max(heights)

        merged_image = Image.new("RGBA", (total_width, max_height), color=(255, 255, 255, 255))

        x_offset = 0
        for image in images:
            merged_image.paste(image, (x_offset, 0))
            x_offset += image.size[0]

        out_path = TempFileManager.mktmp(suffix=".png")
        merged_image.save(out_path)

        return Frame(self._year, out_path)
