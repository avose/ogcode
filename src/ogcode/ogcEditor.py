################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the geometry editor.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents

################################################################################################

class ogcEditor(wx.Window):

    def __init__(self, parent):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditor, self).__init__(parent,style=style)
        self.message = "TODO: Geometry Editor Here."
        self.SetBackgroundColour((0,0,0))
        box_main = wx.BoxSizer(wx.VERTICAL)
        box_panel = wx.BoxSizer(wx.HORIZONTAL)
        p_message = wx.Panel(self, style=wx.RAISED_BORDER)
        p_message.SetBackgroundColour((192,192,192))
        box_messg = wx.BoxSizer(wx.VERTICAL)
        self.st_message = wx.StaticText(p_message, wx.ID_ANY, self.message)
        box_messg.Add(self.st_message, 1, wx.ALL, 20)
        p_message.SetSizerAndFit(box_messg)
        box_panel.Add(p_message, 1, wx.ALIGN_CENTER)
        box_main.Add(box_panel, 1, wx.ALIGN_CENTER)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

################################################################################################
