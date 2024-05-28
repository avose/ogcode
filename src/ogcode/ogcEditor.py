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
from .ogcSettings import ogcSettings

################################################################################################

class ogcEditor(wx.Window):

    def __init__(self, parent, gcode):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditor, self).__init__(parent,style=style)
        self.min_size = [640, 480]
        self.SetMinSize(self.min_size)
        self.gcode = gcode
        self.dc_buffer = wx.Bitmap(*self.Size)
        self.color_fg = ogcSettings.Get('editor_fgcolor')
        self.color_bg = ogcSettings.Get('editor_bgcolor')
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Show(True)
        self.Compile()
        return

    def Compile(self):
        self.gcode_tl, self.gcode_br = self.gcode.bounds()
        self.gcode_w = self.gcode_br[0] - self.gcode_tl[0]
        self.gcode_h = self.gcode_br[1] - self.gcode_tl[1]
        coord_names = ('X','Y','Z')
        coords = [ (0,0,0) ]
        self.geom_lines = []
        self.geom_points = []
        for command in self.gcode.commands:
            if command.code.name == 'G' and command.code.value in [0, 1]:
                arg_coords = { arg.name:arg.value for arg in command.args if arg.name in coord_names }
                x = arg_coords.get('X', coords[-1][0])
                y = arg_coords.get('Y', coords[-1][1])
                z = arg_coords.get('Z', coords[-1][2])
                if coords[-1][2] < 0:
                    self.geom_lines.append( (coords[-1][0], coords[-1][1], x, y) )
                    self.geom_points.append( (x, y) )
                coords.append( (x,y,z) )
        return

    def ScalePoint(self, x, y):
        x = int((x-self.gcode_tl[0]) / self.gcode_w * self.Size[0])
        y = int((y-self.gcode_tl[1]) / self.gcode_h * self.Size[1])
        return x, y

    def Draw(self, dc):
        dc.SetTextForeground(self.color_fg)
        dc.SetPen(wx.Pen(self.color_fg))
        dc.SetBrush(wx.Brush(self.color_fg))
        for line in self.geom_lines:
            x0, y0 = self.ScalePoint(line[0], line[1])
            x1, y1 = self.ScalePoint(line[2], line[3])
            dc.DrawLine(x0, y0, x1, y1)
        dc.SetPen(wx.Pen((255,255,0)))
        dc.SetBrush(wx.Brush((255,255,0)))
        for point in self.geom_points:
            x0, y0 = self.ScalePoint(*point)
            dc.DrawCircle(x0, y0, 1)
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

class ogcEditorPanel(wx.Window):

    def __init__(self, parent, gcode):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditorPanel, self).__init__(parent,style=style)
        self.gcode = gcode
        self.SetBackgroundColour((0,0,0))
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.editor = ogcEditor(self, self.gcode)
        box_main.Add(self.editor, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

################################################################################################
