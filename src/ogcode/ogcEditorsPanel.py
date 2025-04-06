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

################################################################
# Custom toolbar is used, as the default GTK toolbar creates
# spurious warning prints to the console about negative sizes.
class ogcToolbar(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        # Horizontal layout for toolbar buttons.
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        # Define toolbar buttons as tuples or None for a separator:
        # (ID, Tooltip, Icon name, Event handler).
        tools = [
            (parent.ID_CLOSE, "Close Tab", 'cross', parent.OnToolTabClose),
            (parent.ID_NEW, "New Tab", 'page_add', parent.OnToolTabNew),
            (parent.ID_SAVE, "Save G-Code", 'disk', parent.OnToolSave),
            None,
            (EditorTool.ROT_ACLOCK, "Rotate Anti-Clockwise", 'rotate_anticlockwise', parent.OnToolRotAClk),
            (EditorTool.ROT_CLOCK, "Rotate Clockwise", 'rotate_clockwise', parent.OnToolRotClk),
            (EditorTool.FLIP_H, "Flip Horizontal", 'flip_horizontal', parent.OnToolFlipH),
            (EditorTool.FLIP_V, "Flip Vertical", 'flip_vertical', parent.OnToolFlipV),
            None,
            (EditorTool.ZOOM_IN, "Zoom In", 'zoom_in', parent.OnToolZoomIn),
            (EditorTool.ZOOM_DEF, "Zoom Default", 'zoom', parent.OnToolZoomDef),
            (EditorTool.ZOOM_OUT, "Zoom Out", 'zoom_out', parent.OnToolZoomOut),
            None,
            (parent.ID_ENGRAVE, "Engrave", 'page_go', parent.OnToolEngrave),
        ]
        # Create and add buttons or separators to the sizer.
        self.buttons = {}
        for item in tools:
            if item is None:
                separator = wx.StaticLine(self, style=wx.LI_VERTICAL)
                sizer.Add(separator, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 2)
                continue
            tid, label, icon, handler = item
            bmp = ogcIcons.Get(icon)
            btn = wx.BitmapButton(self, id=tid, bitmap=bmp, name=label, style=wx.BORDER_NONE)
            btn.SetToolTip(label)
            btn.Bind(wx.EVT_BUTTON, handler)
            sizer.Add(btn, 0, wx.ALL, 1)
            self.buttons[tid] = btn
        # Finalize layout.
        self.SetSizerAndFit(sizer)
        # Bind paint event for custom background.
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        return

    def OnPaint(self, event):
        # Create vertical gradient from light gray to darker gray.
        dc = wx.PaintDC(self)
        width, height = self.GetClientSize()
        top_color = wx.Colour(240, 240, 240)
        bottom_color = wx.Colour(200, 200, 200)
        dc.GradientFillLinear(wx.Rect(0, 0, width, height), top_color, bottom_color, wx.SOUTH)
        # Draw 1px black border on the bottom.
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), width=1))
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawLine(0, height-1, width, height-1)
        event.Skip()
        return

################################################################
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
        # Create custom toolbar using buttons.
        self.toolbar = ogcToolbar(self)
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
