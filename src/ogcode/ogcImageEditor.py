################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the image editor.
'''
################################################################################################

import wx
import numpy as np
from itertools import chain

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcSettings import ogcSettings
from .ogcImage import ogcImage

################################################################################################

ThresholdChangeEvent, EVT_THRESHOLD_CHANGE = wx.lib.newevent.NewEvent()
ShowImageChangeEvent, EVT_SHOW_IMAGE_CHANGE = wx.lib.newevent.NewEvent()
ShowContoursChangeEvent, EVT_SHOW_CONTOURS_CHANGE = wx.lib.newevent.NewEvent()

################################################################################################

class ogcImageEditorViewer(wx.Panel):
    def __init__(self, parent, image):
        # Initialize the panel and set minimum size
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super().__init__(parent, style=style)
        self.SetMinSize((640, 480))
        # Save original image and build intermediate representation.
        self.orig_image = ogcImage(image)
        self.ir_size = 1024
        self.ir_image = ogcImage(self.orig_image, width=self.ir_size, height=self.ir_size)
        self.canny_min = 100
        self.canny_max = 200
        self.ir_edges = ogcImage(self.ir_image).Edges(self.canny_min, self.canny_max)
        # Rendering settings.
        self.bitmap = None
        self.dc_buffer = wx.Bitmap(*self.Size)
        self.color_fg = ogcSettings.Get("editor_fgcolor")
        self.color_bg = ogcSettings.Get("editor_bgcolor")
        self.dirty = True
        self.show_image = True
        self.show_contours = True
        # Bind event handlers.
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(EVT_THRESHOLD_CHANGE, self.OnThresholdChange)
        self.Bind(EVT_SHOW_IMAGE_CHANGE, self.OnShowImageChange)
        self.Bind(EVT_SHOW_CONTOURS_CHANGE, self.OnShowContoursChange)
        wx.CallAfter(self.OnSize)

    def ProcessImage(self):
        # Process and resize the image for edge detection.
        self.image = ogcImage(self.ir_image)
        dims = (self.Size[0], None) if self.Size[0] < self.Size[1] else (None, self.Size[1])
        self.image.Resize(*dims)
        self.bitmap = wx.Bitmap(self.image.WXImage())

    def OnThresholdChange(self, event):
        # Update edge detection threshold and mark for redraw.
        self.dirty = True
        self.canny_min = event.min_value
        self.canny_max = event.max_value

    def OnShowImageChange(self, event):
        # Toggle image display.
        if self.show_image != event.value:
            self.dirty = True
            self.show_image = event.value

    def OnShowContoursChange(self, event):
        # Toggle contour display.
        if self.show_contours != event.value:
            self.dirty = True
            self.show_contours = event.value

    def Draw(self, dc):
        if self.bitmap is not None:
            # Compute offsets to center the image.
            xoff = (self.Size[0] - self.bitmap.GetWidth()) // 2
            yoff = (self.Size[1] - self.bitmap.GetHeight()) // 2
            # Draw image if enabled.
            if self.show_image:
                dc.DrawBitmap(self.bitmap, xoff, yoff)

            # Draw contours if enabled.
            if self.show_contours:
                dc.SetPen(wx.Pen((0, 255, 0)))
                dc.SetBrush(wx.Brush((255, 255, 0)))
                # Convert contours to NumPy arrays and scale to fit the bitmap.
                contours = [np.array(contour) for contour in self.ir_edges.contours]
                if contours:
                    contours = [
                        c * [
                            self.bitmap.GetWidth() / self.ir_size,
                            self.bitmap.GetHeight() / self.ir_size
                        ]
                        for c in contours
                    ]
                    contours = [c + [xoff, yoff] for c in contours]
                    # Create line segments from contour points.
                    lines = np.vstack([
                        np.column_stack([c, np.roll(c, -1, axis=0)])
                        for c in contours
                    ]).reshape(-1, 2)
                    dc.DrawLineList(lines.astype(int).reshape(-1, 4).tolist())
                    # Extract and expand points for drawing.
                    all_points = np.vstack(contours).astype(int)
                    expanded_points = np.vstack([
                        all_points + offset
                        for offset in [(-1, -1), (0, -1), (1, -1),
                                       (-1, 0), (0, 0), (1, 0),
                                       (-1, 1), (0, 1), (1, 1)]
                    ])
                    # Draw expanded points in red.
                    dc.SetPen(wx.Pen((255, 0, 0)))
                    dc.DrawPointList(expanded_points.tolist())

            # Draw bounding box around the image.
            dc.SetBrush(wx.Brush((0, 0, 0), wx.TRANSPARENT))
            dc.SetPen(wx.Pen((255, 0, 255)))
            dc.DrawRectangle(xoff, yoff, self.bitmap.GetWidth(), self.bitmap.GetHeight() - 2)

    def OnPaint(self, event):
        # Handle window repaint with double buffering.
        dc = wx.MemoryDC()
        dc.SelectObject(self.dc_buffer)
        dc.Clear()
        dc.SetPen(wx.Pen(self.color_bg))
        dc.SetBrush(wx.Brush(self.color_bg))
        dc.DrawRectangle(0, 0, self.Size[0], self.Size[1])
        self.Draw(dc)
        del dc
        dc = wx.BufferedPaintDC(self, self.dc_buffer)

    def OnSize(self, event=None):
        # Mark for redraw when window is resized.
        self.dirty = True

    def OnIdle(self, event):
        # Redraw when idle if necessary.
        if self.dirty:
            self.dirty = False
            self.dc_buffer = wx.Bitmap(*self.Size)
            self.ProcessImage()
            self.Refresh()
            self.Update()

################################################################################################

class ogcImageEditorController(wx.Panel):

    def __init__(self, parent, image):
        style = wx.BORDER_NONE
        super(ogcImageEditorController, self).__init__(parent, style=style)
        self.min_size = [150, 480]
        self.SetMinSize(self.min_size)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND))
        # Main horizontal sizer.
        box_main = wx.BoxSizer(wx.HORIZONTAL)

        # Thin black border on the left.
        border = wx.Panel(self, size=(2, -1), style=style)
        border.SetBackgroundColour(wx.Colour(0, 0, 0))
        box_main.Add(border, 0, wx.EXPAND | wx.RIGHT, 2)

        content = wx.Panel(self, style=style)
        box_content = wx.BoxSizer(wx.VERTICAL)

        # IR Size input field.
        ir_size_label = wx.StaticText(content, label="IR Size:")
        self.ir_size_ctrl = wx.TextCtrl(content, style=wx.TE_PROCESS_ENTER, size=(50, -1))

        # Threshold min slider with label.
        threshold_min_label = wx.StaticText(content, label="Threshold Min:")
        self.threshold_min_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.threshold_min_slider.SetValue(100)
        self.threshold_min_value = wx.StaticText(content, label="100", size=(30, -1))

        # Threshold max slider with label.
        threshold_max_label = wx.StaticText(content, label="Threshold Max:")
        self.threshold_max_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.threshold_max_slider.SetValue(200)
        self.threshold_max_value = wx.StaticText(content, label="200", size=(30, -1))

        # Horizontal sizer for min slider and its value display.
        box_min_slider = wx.BoxSizer(wx.HORIZONTAL)
        box_min_slider.Add(self.threshold_min_slider, 1, wx.EXPAND | wx.RIGHT, 1)
        box_min_slider.Add(self.threshold_min_value, 0, wx.ALIGN_CENTER_VERTICAL)

        # Horizontal sizer for max slider and its value display.
        box_max_slider = wx.BoxSizer(wx.HORIZONTAL)
        box_max_slider.Add(self.threshold_max_slider, 1, wx.EXPAND | wx.RIGHT, 1)
        box_max_slider.Add(self.threshold_max_value, 0, wx.ALIGN_CENTER_VERTICAL)

        # Checkboxes for "Show Image" and "Show Contours".
        self.show_image_checkbox = wx.CheckBox(content, label="Show Image")
        self.show_contours_checkbox = wx.CheckBox(content, label="Show Contours")
        self.show_image_checkbox.SetValue(True)
        self.show_contours_checkbox.SetValue(True)

        # Adding elements to the content sizer.
        box_content.Add(ir_size_label, 0, wx.LEFT | wx.TOP, 2)
        box_content.Add(self.ir_size_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
        box_content.Add(threshold_min_label, 0, wx.LEFT | wx.TOP, 2)
        box_content.Add(box_min_slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
        box_content.Add(threshold_max_label, 0, wx.LEFT | wx.TOP, 0)
        box_content.Add(box_max_slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 1)
        box_content.Add(self.show_image_checkbox, 0, wx.LEFT | wx.TOP, 2)
        box_content.Add(self.show_contours_checkbox, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 2)

        content.SetSizer(box_content)
        box_main.Add(content, 1, wx.EXPAND)
        self.SetSizer(box_main)

        # Bind IR size input field.
        self.ir_size_ctrl.Bind(wx.EVT_TEXT_ENTER, self.OnIRSizeChange)
        # Bind slider movement events.
        self.threshold_min_slider.Bind(wx.EVT_SLIDER, self.OnThresholdChange)
        self.threshold_max_slider.Bind(wx.EVT_SLIDER, self.OnThresholdChange)
        # Bind checkbox events.
        self.show_image_checkbox.Bind(wx.EVT_CHECKBOX, self.OnShowImageChange)
        self.show_contours_checkbox.Bind(wx.EVT_CHECKBOX, self.OnShowContoursChange)

        self.Show(True)

    def OnIRSizeChange(self, event):
        # Handle IR size change event.
        return

    def OnThresholdChange(self, event):
        min_value = self.threshold_min_slider.GetValue()
        max_value = self.threshold_max_slider.GetValue()
        # Ensure max is always greater than min.
        if min_value >= max_value:
            if event.EventObject == self.threshold_min_slider:
                max_value = min_value + 1
                self.threshold_max_slider.SetValue(max_value)
            else:
                min_value = max_value - 1
                self.threshold_min_slider.SetValue(min_value)
        # Update displayed values when sliders move.
        self.threshold_min_value.SetLabel(str(min_value))
        self.threshold_max_value.SetLabel(str(max_value))
        # Post event to parent.
        threshold_event = ThresholdChangeEvent(min_value=min_value, max_value=max_value)
        wx.PostEvent(self.Parent, threshold_event)
        return

    def OnShowImageChange(self, event):
        # Get current checkbox value.
        show_image_value = self.show_image_checkbox.GetValue()
        # Post event to notify parent of "Show Image" checkbox state change.
        show_image_event = ShowImageChangeEvent(value=show_image_value)
        wx.PostEvent(self.Parent, show_image_event)
        return

    def OnShowContoursChange(self, event):
        # Get current checkbox value.
        show_contours_value = self.show_contours_checkbox.GetValue()
        # Post event to notify parent of "Show Contours" checkbox state change.
        show_contours_event = ShowContoursChangeEvent(value=show_contours_value)
        wx.PostEvent(self.Parent, show_contours_event)
        return

################################################################################################

class ogcImageEditorPanel(wx.Panel):

    def __init__(self, parent, image):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcImageEditorPanel, self).__init__(parent,style=style)
        self.image = image
        self.SetBackgroundColour((0,0,0))
        box_main = wx.BoxSizer(wx.HORIZONTAL)
        self.viewer = ogcImageEditorViewer(self, self.image)
        box_main.Add(self.viewer, 1, wx.EXPAND)
        box_controller = wx.BoxSizer(wx.VERTICAL)
        self.controller = ogcImageEditorController(self, self.image)
        box_controller.Add(self.controller, 1, wx.EXPAND)
        box_main.Add(box_controller, 0, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Bind(EVT_THRESHOLD_CHANGE, self.OnThresholdChange)
        self.Bind(EVT_SHOW_IMAGE_CHANGE, self.OnShowImageChange)
        self.Bind(EVT_SHOW_CONTOURS_CHANGE, self.OnShowContoursChange)
        self.Show(True)
        return

    def OnThresholdChange(self, event):
        # Forward threshold event to the viewer.
        viewer_event = ThresholdChangeEvent(min_value=event.min_value, max_value=event.max_value)
        wx.PostEvent(self.viewer, viewer_event)
        return

    def OnShowImageChange(self, event):
        # Forward show image event to the viewer.
        show_image_event = ShowImageChangeEvent(value=event.value)
        wx.PostEvent(self.viewer, show_image_event)

    def OnShowContoursChange(self, event):
        # Forward show contours event to the viewer.
        show_contours_event = ShowContoursChangeEvent(value=event.value)
        wx.PostEvent(self.viewer, show_contours_event)

################################################################################################
