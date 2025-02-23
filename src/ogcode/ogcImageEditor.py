################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the image editor.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcSettings import ogcSettings

################################################################################################

class ogcImageEditor(wx.Window):

    def __init__(self, parent, image):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcImageEditor, self).__init__(parent,style=style)
        self.min_size = [640, 480]
        self.SetMinSize(self.min_size)
        self.image = image
        self.bitmap = wx.Bitmap(self.image)
        self.dc_buffer = wx.Bitmap(*self.Size)
        self.color_fg = ogcSettings.Get('editor_fgcolor')
        self.color_bg = ogcSettings.Get('editor_bgcolor')
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Show(True)
        return

    def Draw(self, dc):
        dc.DrawBitmap(self.bitmap, 0, 0)
        return

    def OnPaint(self, event):
        # Paint with double buffering.
        dc = wx.MemoryDC()
        dc.SelectObject(self.dc_buffer)
        dc.Clear()
        dc.SetPen(wx.Pen(self.color_bg))
        dc.SetBrush(wx.Brush(self.color_bg))
        dc.DrawRectangle(0, 0, self.Size[0], self.Size[1])
        self.Draw(dc)
        del dc
        dc = wx.BufferedPaintDC(self, self.dc_buffer)
        return

    def OnSize(self, event):
        self.dc_buffer = wx.Bitmap(*self.Size)
        self.Refresh()
        return

################################################################################################

class ogcImageEditorPanel(wx.Window):

    def __init__(self, parent, image):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcImageEditorPanel, self).__init__(parent,style=style)
        self.image = image
        self.SetBackgroundColour((0,0,0))
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.editor = ogcImageEditor(self, self.image)
        box_main.Add(self.editor, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

################################################################################################
