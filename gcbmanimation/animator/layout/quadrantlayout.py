from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from gcbmanimation.animator.frame import Frame
from gcbmanimation.util.tempfile import mktmp
Image.MAX_IMAGE_PIXELS = None

class Quadrant:

    def __init__(self, x_origin, y_origin, width, height, title=None):
        self.x_origin = x_origin
        self.y_origin = y_origin
        self.width = width
        self.height = height
        self.title = title


class QuadrantLayout:

    def __init__(self, q1_pct, q2_pct, q3_pct, q4_pct, margin=0.05):
        self._q1_pct = q1_pct
        self._q2_pct = q2_pct
        self._q3_pct = q3_pct
        self._q4_pct = q4_pct
        self._margin = margin

    def render(
        self, q1_frame, q2_frame, q3_frame, q4_frame,
        q1_label=None, q2_label=None, q3_label=None, q4_label=None,
        title=None, dimensions=None
    ):
        width, height = dimensions or (640, 480)
        canvas_width = int(width * (1 - self._margin))
        canvas_height = int(height * (1 - self._margin))
        canvas_x_min = (width - canvas_width) // 2
        canvas_x_max = width - (width - canvas_width) // 2
        canvas_y_min = (height - canvas_height) // 2
        canvas_y_max = height - (height - canvas_height) // 2

        image = Image.new("RGBA", dimensions, (255, 255, 255, 255))

        if title:
            title_font_size = 100
            title_font = ImageFont.truetype("arial.ttf", title_font_size)
            title_w, title_h = title_font.getsize(title)
            true_title_height = int(title_h) + int(height * 0.01)
            
            title_x = width // 2 - title_w // 2
            title_y = int(height * self._margin / 2) - title_h // 2
            ImageDraw.Draw(image).text((title_x, title_y), title, (0, 0, 0), font=title_font)

            canvas_height -= true_title_height // 2
            canvas_y_min += true_title_height // 2

        quadrants = [
            Quadrant(canvas_x_min,
                     canvas_y_min,
                     int(self._q1_pct[0] / 100 * canvas_width),
                     int(self._q1_pct[1] / 100 * canvas_height),
                     q1_label),
            Quadrant(int(canvas_x_max - self._q2_pct[0] / 100 * canvas_width),
                     canvas_y_min,
                     int(self._q2_pct[0] / 100 * canvas_width),
                     int(self._q2_pct[1] / 100 * canvas_height),
                     q2_label),
            Quadrant(canvas_x_min,
                     int(canvas_y_max - self._q3_pct[1] / 100 * canvas_height),
                     int(self._q3_pct[0] / 100 * canvas_width),
                     int(self._q3_pct[1] / 100 * canvas_height),
                     q3_label),
            Quadrant(int(canvas_x_max - self._q4_pct[0] / 100 * canvas_width),
                     int(canvas_y_max - self._q4_pct[1] / 100 * canvas_height),
                     int(self._q4_pct[0] / 100 * canvas_width),
                     int(self._q4_pct[1] / 100 * canvas_height),
                     q4_label)]

        for i, frame in enumerate((q1_frame, q2_frame, q3_frame, q4_frame)):
            self._render_quadrant(image, quadrants[i], frame)

        out_path = mktmp(suffix=".png")
        image.save(out_path)

        return Frame(q1_frame.year, out_path)
    
    def _render_quadrant(self, base_image, quadrant, frame):
        true_title_height = 0
        if quadrant.title:
            base_width, base_height = base_image.size
            font_size = 60
            font = ImageFont.truetype("arial.ttf", font_size)
            title_width, title_height = font.getsize(quadrant.title)
            true_title_height = int(title_height) + int(base_height * 0.01)
            title_x_pos = int(quadrant.x_origin + quadrant.width / 2 - title_width / 2)
            title_y_pos = int(quadrant.y_origin + true_title_height // 2)
            ImageDraw.Draw(base_image).text((title_x_pos, title_y_pos), quadrant.title, (0, 0, 0, 255), font=font)

        frame_image = Image.open(frame.path)
        new_width, new_height = self._calculate_best_fit(frame_image, quadrant, true_title_height)
        frame_image_resized = frame_image.resize((new_width, new_height), Image.ANTIALIAS)
        x_offset = (quadrant.width - new_width) // 2
        x_pos = quadrant.x_origin + x_offset
        y_offset = (quadrant.height - new_height) // 2
        y_pos = quadrant.y_origin + y_offset + true_title_height // 2
        base_image.paste(frame_image_resized, (x_pos, y_pos))
    
    def _calculate_best_fit(self, image, quadrant, top_margin=0):
        # Resize the image to take up the maximum available space inside the quadrant.
        original_width, original_height = image.size
        aspect_ratio = original_width / original_height

        max_x = int(quadrant.width * (1 - self._margin * 2))
        max_y = int(quadrant.height * (1 - self._margin * 2)) - top_margin

        if aspect_ratio > 1:
            new_width = int(quadrant.width * (1 - self._margin * 2))
            new_height = int(new_width / aspect_ratio)
            if new_height > max_y:
                new_height = max_y
                new_width = int(new_height * aspect_ratio)
        else:
            new_height = max_y
            new_width = int(new_height / aspect_ratio)
            if new_width > max_x:
                new_width = int(quadrant.width * (1 - self._margin * 2))
                new_height = int(new_width * aspect_ratio)

        return new_width, new_height
