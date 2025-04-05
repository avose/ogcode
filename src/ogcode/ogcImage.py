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
from .ogcVector import (
    contours_to_lines,
    bresenham_line,
    simplify_lines,
    flip_lines,
    rotate_lines
)

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

    ################################################################
    # Rotate the image either clockwise or counter-clockwise.
    def Rotate(self, clockwise=True):
        # Save original shape before rotation
        h, w = self.cv_image.shape[:2]
        if clockwise:
            self.cv_image = cv2.rotate(self.cv_image, cv2.ROTATE_90_CLOCKWISE)
        else:
            self.cv_image = cv2.rotate(self.cv_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # Rotate associated lines
        if hasattr(self, 'lines') and self.lines.size > 0:
            self.lines = rotate_lines(self.lines, height=h, width=w, clockwise=clockwise)
        return self

    ################################################################
    # Flip the image either vertically or horizontally.
    def Flip(self, vertical=True):
        # Save original shape before flip
        h, w = self.cv_image.shape[:2]
        if vertical:
            self.cv_image = cv2.flip(self.cv_image, 0)  # Flip vertically
        else:
            self.cv_image = cv2.flip(self.cv_image, 1)  # Flip horizontally
        # Flip associated lines
        if hasattr(self, 'lines') and self.lines.size > 0:
            self.lines = flip_lines(self.lines, height=h, width=w, vertical=vertical)
        return self

################################################################################################
