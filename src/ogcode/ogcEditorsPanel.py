################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the notebook panel and toolbar.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcPlaceHolder import ogcPlaceHolder
from .ogcEditorsNotebook import ogcEditorsNotebook

################################################################################################

class ogcEditorsPanel(wx.Window):
    ID_NEW         = 1001
    ID_COPY        = 1002
    ID_PASTE       = 1003
    ID_ZOOM_IN     = 1004
    ID_ZOOM_OUT    = 1005
    ID_EXIT        = 1006

    def __init__(self, parent):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditorsPanel, self).__init__(parent,style=style)
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        tools = [ (self.ID_EXIT, "Close Tab", 'cross', self.OnToolTabClose),
                  (self.ID_NEW, "New Tab", 'page_add', self.OnToolTabNew),
                  (self.ID_COPY, "Copy", 'page_copy', self.OnToolCopy),
                  (self.ID_PASTE, "Paste", 'page_paste', self.OnToolPaste),
                  (self.ID_ZOOM_OUT, "Zoom Out", 'zoom_out', self.OnToolZoomOut),
                  (self.ID_ZOOM_IN, "Zoom In", 'zoom_in', self.OnToolZoomIn) ]
        for tool in tools:
            tid, text, icon, callback = tool
            self.toolbar.AddTool(tid, text, ogcIcons.Get(icon), wx.NullBitmap,
                                 wx.ITEM_NORMAL, text, text, None)
            self.Bind(wx.EVT_TOOL, callback, id=tid)
        self.toolbar.Realize()
        box_main.Add(self.toolbar, 0, wx.EXPAND)
        self.notebook = ogcEditorsNotebook(self)
        box_main.Add(self.notebook, 1, wx.TOP | wx.BOTTOM | wx.EXPAND, 0)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def OnToolTabNew(self, event):
        print("TODO: Toolbar: New Tab.")
        return

    def OnToolTabClose(self, event):
        print("TODO: Toolbar: Close current tab.")
        return

    def OnToolPaste(self, event):
        print("TODO: Toolbar: Paste.")
        return

    def OnToolCopy(self, event):
        print("TODO: Toolbar: Copy.")
        return

    def OnToolZoomIn(self, event):
        print("TODO: Toolbar: Zoom in.")
        return

    def OnToolZoomOut(self, event):
        print("TODO: Toolbar: Zoom out.")
        return

    def NewTab(self, data):
        self.notebook.NewTab(data)
        return

################################################################################################
