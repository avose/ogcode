################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the loading PNG icon images.
'''
################################################################################################

import wx
import os

################################################################################################

class ogcIconManager():
    __icons = None

    def __init__(self):
        if ogcIconManager.__icons is not None:
            return
        ogcIconManager.__icons = {}
        img_dir = os.path.dirname(os.path.abspath(__file__))
        img_dir = os.path.join(img_dir,"icons")
        for fname in os.listdir(img_dir):
            img_name, ext = os.path.splitext(fname)
            if ext != ".png":
                continue
            img_path = os.path.join(img_dir, fname)
            bmp = wx.Bitmap(wx.Image(img_path, wx.BITMAP_TYPE_ANY))
            ogcIconManager.__icons[img_name] = bmp
        return

    def Get(self, name):
        if name in ogcIconManager.__icons:
            return ogcIconManager.__icons[name]
        return None

################################################################################################

ogcIcons = ogcIconManager()

################################################################################################
