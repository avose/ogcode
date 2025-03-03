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
            self.cv_image = np.zeros((height, width, 3), dtype=np.int8)

        # Resize to specified size if needed.
        if width is not None or height is not None:
            self.Resize(width, height, interp)
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
    def Shape(self):
        return (self.cv_image.shape[1], self.cv_image.shape[0])

    ################################################################
    # Return image width.
    def Width(self):
        return self.cv_image.shape[1]

    ################################################################
    # Return image height.
    def Height(self):
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
    def Edges(self):
        grayscale = cv2.cvtColor(self.cv_image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(grayscale, 100, 200)
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

################################################################################################
