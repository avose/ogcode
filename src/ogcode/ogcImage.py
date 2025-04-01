################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds image modification utilities.
'''
################################################################################################

import wx
import cv2
import numpy as np
from typing import List, Tuple

from .ogcSettings import ogcSettings

################################################################################################

def contours_to_lines(contours: List[np.ndarray]) -> List[np.ndarray]:
    # Convert contours into individual line segments including closing edge.
    lines = []
    for contour in contours:
        if len(contour) < 2:
            continue
        start_points = contour
        end_points = np.roll(contour, -1, axis=0)
        segment_pairs = np.stack([start_points, end_points], axis=1)
        lines.extend(segment_pairs)
    return lines


def bresenham_line(p0, p1):
    # Bresenham's line algorithm for integer pixel coordinates.
    x0, y0 = p0
    x1, y1 = p1
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        points.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy
    return points


def simplify_lines(
        lines: List[np.ndarray],
        edges: np.ndarray,
        scale: float = 0.5
) -> Tuple[List[np.ndarray], np.ndarray]:
    # Simplify lines by rasterizing them onto a low-resolution canvas and
    # extracting only contributing segments.
    if not lines:
        return [], edges

    orig_height, orig_width = edges.shape[:2]
    width = int(orig_width * scale)
    height = int(orig_height * scale)

    height, width = edges.shape[:2]
    min_xy = np.array([0.0, 0.0])
    max_xy = np.array([width, height], dtype=float)
    span = max_xy - min_xy

    canvas = np.zeros((height, width), dtype=bool)
    lines_array = np.stack(lines)
    norm_points = (lines_array - min_xy) / span
    #scaled_points = (norm_points * np.array([width - 1, height - 1])).astype(int)
    scaled_points = ((norm_points * [width, height]) - 0.5).astype(int)

    diffs = scaled_points[:, 1] - scaled_points[:, 0]
    lengths = np.linalg.norm(diffs, axis=1)
    sort_indices = np.argsort(-lengths)
    sorted_scaled = scaled_points[sort_indices]
    sorted_original = lines_array[sort_indices]

    kept_segments = []

    for i in range(sorted_scaled.shape[0]):
        p1_canvas, p2_canvas = sorted_scaled[i]
        line_pixels = bresenham_line(tuple(p1_canvas), tuple(p2_canvas))

        start_pixel = None
        last_pixel = None

        for x, y in line_pixels:
            if 0 <= y < height and 0 <= x < width:
                if not canvas[y, x]:
                    canvas[y, x] = True
                    if start_pixel is None:
                        start_pixel = (x, y)
                    last_pixel = (x, y)
                else:
                    if start_pixel is not None and last_pixel is not None:
                        p_start = ((np.array(start_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
                        p_end = ((np.array(last_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
                        kept_segments.append(np.array([p_start, p_end]))
                        start_pixel = None
                        last_pixel = None

        if start_pixel is not None and last_pixel is not None:
            p_start = ((np.array(start_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
            p_end = ((np.array(last_pixel) + 0.5) / [width, height]) * [orig_width, orig_height]
            kept_segments.append(np.array([p_start, p_end]))

    # Convert boolean canvas to uint8 RGB image for visualization.
    canvas_image = (canvas.astype(np.uint8) * 255)
    edges_rgb = cv2.cvtColor(canvas_image, cv2.COLOR_GRAY2RGB)
    edges_resized = cv2.resize(edges_rgb, (orig_width, orig_height), interpolation=cv2.INTER_NEAREST)

    return kept_segments, edges_resized

################################################################################################

class ogcImage():

    ################################################################
    # Constants.
    INTER_CUBIC = cv2.INTER_CUBIC
    INTER_AREA  = cv2.INTER_AREA

    ################################################################
    # Constructor.
    def __init__(self, image = None, width = None, height = None, interp = cv2.INTER_CUBIC):
        # Create an OpenCV image from provided source or create empty.
        if image is not None:
            # Use the provided image if there is one.
            if isinstance(image, wx.Image):
                # Image is a WxPython image.
                self.cv_image = self.WXToCV2Image(image)
            elif isinstance(image, ogcImage):
                # Image is an OGCode image.
                self.cv_image = image.CV2Image()
            else:
                # Assume an OpenCV image (numpy object).
                self.cv_image = np.copy(image)
        else:
            # Require width and height to create an empty image.
            self.cv_image = np.zeros((height, width, 3), dtype=np.uint8)

        # Resize to specified size if needed.
        if width is None or height is None:
            self.Resize(width, height, interp)
        else:
            self.ResizeCanvas(width=width, height=height, interp=interp)
        return

    ################################################################
    # Static: Convert a WxPython image to an OpenCV image.
    @staticmethod
    def WXToCV2Image(wx_image):
        cv_image = np.frombuffer(wx_image.GetDataBuffer(), dtype='uint8')
        cv_image = cv_image.reshape( (wx_image.GetHeight(), wx_image.GetWidth(), 3) )
        return cv_image

    ################################################################
    # Static: Convert an OpenCV image to a WxPython image.
    @staticmethod
    def CV2ToWXImage(cv_image):
        wx_image = wx.Image(cv_image.shape[1], cv_image.shape[0])
        wx_image.SetData(cv_image.tostring())
        return wx_image

    ################################################################
    # Return image shape as (width, height).
    @property
    def shape(self):
        return (self.cv_image.shape[1], self.cv_image.shape[0])

    ################################################################
    # Return image width.
    @property
    def width(self):
        return self.cv_image.shape[1]

    ################################################################
    # Return image height.
    @property
    def height(self):
        return self.cv_image.shape[0]

    ################################################################
    # Return image as a WxPython Image object.
    def WXImage(self):
        return self.CV2ToWXImage(self.cv_image)

    ################################################################
    # Return image as a OpenCV image object.
    def CV2Image(self):
        return np.copy(self.cv_image)

    ################################################################
    # Replace image contents with cleaned image (w.r.t edges)
    def Cleanup(self, scale: float = 0.95) -> np.ndarray:
        # Create a padded version of the image by shrinking and
        # centering it to reduce edge artifacts.
        original_height, original_width = self.cv_image.shape[:2]
        new_width = int(original_width * scale)
        new_height = int(original_height * scale)
        resized = cv2.resize(self.cv_image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        # Use the first pixel color as the background fill color.
        bg_color = self.cv_image[0, 0].tolist()
        padded = np.full_like(self.cv_image, bg_color, dtype=np.uint8)
        x_offset = (original_width - new_width) // 2
        y_offset = (original_height - new_height) // 2
        padded[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized
        self.cv_image = padded
        return self

    ################################################################
    # Replace image contents with image edges and return self.
    def Edges(self, threshold_min: int = 100, threshold_max: int = 200):
        # Convert to grayscale.
        grayscale = cv2.cvtColor(self.cv_image, cv2.COLOR_RGB2GRAY)
        # Extract edges.
        edges = cv2.Canny(grayscale, threshold_min, threshold_max)
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        # Find contours.
        contours = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0]
        contours = [ c.reshape( (c.shape[0], 2) ) for c in contours ]
        # Convert contours to lines.
        self.lines = contours_to_lines(contours)
        self.lines, edges_rgb = simplify_lines(
            self.lines,
            edges,
            scale=1
        )
        # Save image of edges.
        self.cv_image = edges_rgb
        return self

    ################################################################
    # Replace image with scaled image and return self.
    def Resize(self, width = None, height = None, interp = cv2.INTER_CUBIC):
        dims = None
        (h, w) = self.cv_image.shape[:2]

        # Neither width nor height specified.
        if width is None and height is None:
            return self

        # Both width and height are specified.
        if width is not None and height is not None:
            self.cv_image = cv2.resize(
                self.cv_image,
                (width, height),
                interpolation = cv2.INTER_CUBIC
            )
            return self

        # Either width or height is specified.
        if width is None:
            # Calculate dimensions from height.
            r = height / float(h)
            dims = (int(w * r), height)
        else:
            # Calculate dimensions from width.
            r = width / float(w)
            dims = (width, int(h * r))
        # Resize image and return self.
        self.cv_image = cv2.resize(self.cv_image, dims, interpolation=interp)
        return self

    ################################################################
    # Replace image with image contents centered in new image and return self.
    def ResizeCanvas(self, width, height, x = 0, y = 0, center = True, interp = cv2.INTER_CUBIC):
        # Collect scaling parameters.
        bg_color = tuple(int(c) for c in self.cv_image[0, 0])
        (oh, ow) = self.cv_image.shape[:2]
        if width - ow >= 0 and height - oh >= 0:
            # Both dims of original are smaller than new canvas size.
            if abs(width - ow) < abs(height - oh):
                # Scale based on width (closest size match).
                dims = (width, None)
            else:
                # Scale based on height (closest size match).
                dims = (None, height)
        elif width - ow < 0 and height - oh < 0:
            # Both dims of original are larger than new canvas size.
            if ow > oh:
                # Scale based on width (largest dim).
                dims = (width, None)
            else:
                # Scale based on height (largest dim).
                dims = (None, height)
        elif width - ow > 0:
            # Original width is smaller than new canvas width.
            dims = (None, height)
        else:
            # Original height is smaller than new canvas height.
            dims = (width, None)

        # Scale original image to fit in new canvas.
        self.Resize(*dims, interp)

        # Save (possibly scaled) original image.
        orig = self.cv_image
        (oh, ow) = orig.shape[:2]

        # Create new image with new canvas size.
        self.cv_image = np.zeros((height, width, 3), dtype=np.uint8)
        self.cv_image[:] = bg_color

        # Compute offsets of original image in new canvas.
        if center:
            x, y = ((width - ow)//2 + x, (height - oh)//2 + y)

        # Copy original image into new canvas and return self.
        self.cv_image[y:y + oh, x:x + ow] = orig
        return self

################################################################################################
