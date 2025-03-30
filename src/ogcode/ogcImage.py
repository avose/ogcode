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

from .ogcSettings import ogcSettings

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
    # Replace image contents with image edges and return self.
    def Edges(self, threshold_min: int = 100, threshold_max: int = 200):
        # Convert to grayscale.
        grayscale = cv2.cvtColor(self.cv_image, cv2.COLOR_RGB2GRAY)
        # Extract edges.
        edges = cv2.Canny(grayscale, threshold_min, threshold_max)
        # Find contours.
        contours = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[0]
        self.contours = [ list(c.reshape( (c.shape[0], 2) )) for c in contours ]
        # Convert back to RGB.
        edges_rgb = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
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

        # Compute offsets of original image in new canvas.
        if center:
            x, y = ((width - ow)//2 + x, (height - oh)//2 + y)

        # Copy original image into new canvas and return self.
        self.cv_image[y:y + oh, x:x + ow] = orig
        return self

################################################################################################
