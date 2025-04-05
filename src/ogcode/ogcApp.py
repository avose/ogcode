################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for managing the main WX-Python App.
'''
################################################################################################

import wx

################################################################################################

class ogcAppManager():
    __wxapp = None

    def __init__(self):
        if ogcAppManager.__wxapp is None:
            ogcAppManager.__wxapp = wx.App(0)
        return

    def get(self):
        return ogcAppManager.__wxapp

################################################################################################

ogcApp = ogcAppManager()

################################################################################################
