################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the image editor.
'''
################################################################################################

import wx
from itertools import tee

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcSettings import ogcSettings
from .ogcImage import ogcImage

################################################################################################

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

################################################################################################

class ogcImageEditorViewer(wx.Window):

    def __init__(self, parent, image):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcImageEditorViewer, self).__init__(parent,style=style)
        self.min_size = [640, 480]
        self.SetMinSize(self.min_size)
        self.orig_image = ogcImage(image)
        self.bitmap = None
        self.dc_buffer = wx.Bitmap(*self.Size)
        self.color_fg = ogcSettings.Get('editor_fgcolor')
        self.color_bg = ogcSettings.Get('editor_bgcolor')
        self.dirty = True
        self.ir_size = 1024
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Show(True)
        wx.CallAfter(self.OnSize)
        return

    def ProcessImage(self):
        # Scale original image to internal representation size.
        self.image = ogcImage(self.orig_image, width=self.ir_size, height=self.ir_size)
        # Find edges.
        self.image = self.image.Edges()
        # Scale image to widget size.
        if self.Size[0] < self.Size[1]:
            dims = (self.Size[0], None)
        else:
            dims = (None, self.Size[1])
        self.image = self.image.Resize(*dims)
        # Convert image to bitmap and redraw widget.
        self.bitmap = wx.Bitmap(self.image.WXImage())
        return

    def Draw(self, dc):
        if self.bitmap is not None:
            # Draw image bitmap in center of widget.
            xoff = (self.Size[0] - self.bitmap.GetWidth()) // 2
            yoff = (self.Size[1] - self.bitmap.GetHeight()) // 2
            dc.DrawBitmap(self.bitmap, xoff, yoff)
            # Draw outline around bitmap.
            dc.SetBrush(wx.Brush((0,0,0), wx.TRANSPARENT))
            dc.SetPen(wx.Pen((255,0,255)))
            dc.DrawRectangle(xoff, yoff, self.bitmap.GetWidth(), self.bitmap.GetHeight()-2)
            # Draw contour lines.
            dc.SetPen(wx.Pen((0,255,0)))
            dc.SetBrush(wx.Brush((0,255,0)))
            for contour in self.image.contours:
                for p0, p1 in pairwise(contour + [contour[0]]):
                    x0, y0 = p0
                    x1, y1 = p1
                    x0 = int(x0/self.ir_size * self.bitmap.GetWidth() + xoff)
                    x1 = int(x1/self.ir_size * self.bitmap.GetWidth() + xoff)
                    y0 = int(y0/self.ir_size * self.bitmap.GetHeight() + yoff)
                    y1 = int(y1/self.ir_size * self.bitmap.GetHeight() + yoff)
                    dc.DrawLine(x0, y0, x1, y1)
            # Draw contour points.
            dc.SetPen(wx.Pen((255,255,0)))
            dc.SetBrush(wx.Brush((255,255,0)))
            for contour in self.image.contours:
                for x, y in contour:
                    x = int(x/self.ir_size * self.bitmap.GetWidth() + xoff)
                    y = int(y/self.ir_size * self.bitmap.GetHeight() + yoff)
                    dc.DrawCircle(x, y, 1)
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

    def OnSize(self, event = None):
        # Set dirty flag to trigger redraw when idle.
        self.dirty = True
        return

    def OnIdle(self, event):
        # Perform a redraw if dirty and idle.
        if self.dirty:
            self.dirty = False
            self.dc_buffer = wx.Bitmap(*self.Size)
            self.ProcessImage()
            self.Refresh()
            self.Update()
        return


################################################################################################

class ogcImageEditorPanel(wx.Window):

    def __init__(self, parent, image):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcImageEditorPanel, self).__init__(parent,style=style)
        self.image = image
        self.SetBackgroundColour((0,0,0))
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.editor = ogcImageEditorViewer(self, self.image)
        box_main.Add(self.editor, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

################################################################################################
