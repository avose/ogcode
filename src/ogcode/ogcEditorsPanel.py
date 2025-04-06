################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the notebook panel and toolbar.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcEditor import EditorTool
from .ogcEvents import ogcEvents
from .ogcPlaceHolder import ogcPlaceHolder
from .ogcEditorsNotebook import ogcEditorsNotebook

################################################################################################

class ogcEditorsPanel(wx.Window):
    ID_CLOSE   = wx.NewIdRef()
    ID_NEW     = wx.NewIdRef()
    ID_SAVE    = wx.NewIdRef()
    ID_ENGRAVE = wx.NewIdRef()

    def __init__(self, parent):
        # Set style and call superclass constructor.
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditorsPanel, self).__init__(parent,style=style)
        # Create top-level sizer.
        box_main = wx.BoxSizer(wx.VERTICAL)
        # Create toolbar.
        self.toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        tools = [
            (self.ID_CLOSE, "Close Tab", 'cross', self.OnToolTabClose),
            (self.ID_NEW, "New Tab", 'page_add', self.OnToolTabNew),
            (self.ID_SAVE, "Save G-Code", 'disk', self.OnToolSave),
            (EditorTool.ROT_ACLOCK, "Rotate Anti-Clockwise", 'rotate_anticlockwise', self.OnToolRotAClk),
            (EditorTool.ROT_CLOCK, "Rotate Clockwise", 'rotate_clockwise', self.OnToolRotClk),
            (EditorTool.FLIP_H, "Flip Horizontal", 'flip_horizontal', self.OnToolFlipH),
            (EditorTool.FLIP_V, "Flip Verical", 'flip_vertical', self.OnToolFlipV),
            (EditorTool.ZOOM_IN, "Zoom In", 'zoom_in', self.OnToolZoomIn),
            (EditorTool.ZOOM_DEF, "Zoom Default", 'zoom', self.OnToolZoomDef),
            (EditorTool.ZOOM_OUT, "Zoom Out", 'zoom_out', self.OnToolZoomOut),
            (self.ID_ENGRAVE, "Engrave", 'page_go', self.OnToolEngrave),
        ]
        for tool in tools:
            tid, text, icon, callback = tool
            self.toolbar.AddTool(tid, text, ogcIcons.Get(icon), wx.NullBitmap,
                                 wx.ITEM_NORMAL, text, text, None)
            self.Bind(wx.EVT_TOOL, callback, id=tid)
        self.toolbar.Realize()
        box_main.Add(self.toolbar, 0, wx.EXPAND)
        # Add editors notebook.
        self.notebook = ogcEditorsNotebook(self)
        box_main.Add(self.notebook, 1, wx.TOP | wx.BOTTOM | wx.EXPAND, 0)
        # Fit.
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def OnToolTabClose(self, event):
        # Close the current tab.
        self.notebook.CloseTab()
        return

    def OnToolTabNew(self, event):
        # Open a new file.
        data, file_path = self.Parent.OpenFileDialog()
        if data is not None and file_path is not None:
            self.NewTab(data, file_path)
        return

    def OnToolSave(self, event):
        # Save G-Code file.
        gcode = self.notebook.CurrentTab().GetGCode()
        if gcode is not None:
            self.Parent.SaveFileDialog(str(gcode))
        return

    def OnToolRotClk(self, event):
        # Rotate clockwise.
        self.notebook.ToolCommand(EditorTool.ROT_CLOCK)
        return

    def OnToolRotAClk(self, event):
        # Rotate anti-clockwise.
        self.notebook.ToolCommand(EditorTool.ROT_ACLOCK)
        return

    def OnToolFlipH(self, event):
        # Flip horizontal.
        self.notebook.ToolCommand(EditorTool.FLIP_H)
        return

    def OnToolFlipV(self, event):
        # Flip vertical.
        self.notebook.ToolCommand(EditorTool.FLIP_V)
        return

    def OnToolZoomIn(self, event):
        # Zoom in.
        self.notebook.ToolCommand(EditorTool.ZOOM_IN)
        return

    def OnToolZoomDef(self, event):
        # Zoom default (and center).
        self.notebook.ToolCommand(EditorTool.ZOOM_DEF)
        return

    def OnToolZoomOut(self, event):
        # Zoom out.
        self.notebook.ToolCommand(EditorTool.ZOOM_OUT)
        return

    def OnToolEngrave(self, event):
        # Engrave.
        self.Parent.OpenEngraveDialog()
        return

    def NewTab(self, data, path):
        # Create a new tab with specified data.
        self.notebook.NewTab(data, path)
        return

    def CurrentTab(self):
        # Returns the current tab.
        return self.notebook.CurrentTab()

################################################################################################
