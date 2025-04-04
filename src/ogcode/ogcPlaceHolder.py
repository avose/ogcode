################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for a placeholder panel to use when no data is present.
'''
################################################################################################

import wx

################################################################################################
class ogcPlaceHolder(wx.Panel):
    def __init__(self, parent, min_size=[16, 16], message=""):
        super(ogcPlaceHolder, self).__init__(parent)
        self.min_size = min_size
        self.SetMinSize(self.min_size)
        self.message = message
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
        box_main.SetMinSize(self.min_size)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def OnClose(self, event=None):
        return

    def GetGCode(self):
        return None

################################################################################################
