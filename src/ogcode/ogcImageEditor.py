################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the image editor.
'''
################################################################################################

import wx
import numpy as np

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcSettings import ogcSettings
from .ogcImage import ogcImage

################################################################################################

ThresholdEvent, EVT_THRESHOLD = wx.lib.newevent.NewEvent()
ShowImageEvent, EVT_SHOW_IMAGE = wx.lib.newevent.NewEvent()
ShowContoursEvent, EVT_SHOW_CONTOURS = wx.lib.newevent.NewEvent()
IRSizeEvent, EVT_IR_SIZE = wx.lib.newevent.NewEvent()

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
        self.Bind(EVT_THRESHOLD, self.OnThresholdChange)
        self.Bind(EVT_IR_SIZE, self.OnIRSizeChange)
        self.Bind(EVT_SHOW_IMAGE, self.OnShowImageChange)
        self.Bind(EVT_SHOW_CONTOURS, self.OnShowContoursChange)
        wx.CallAfter(self.OnSize)
        return

    def ProcessImage(self):
        # Process and resize the image for edge detection.
        self.image = ogcImage(self.ir_image)
        dims = (self.Size[0], None) if self.Size[0] < self.Size[1] else (None, self.Size[1])
        self.image.Resize(*dims)
        self.bitmap = wx.Bitmap(self.image.WXImage())
        return

    def OnIRSizeChange(self, event):
        # Update edge detection threshold and mark for redraw.
        self.dirty = True
        self.ir_size = event.value
        self.ir_image = ogcImage(self.orig_image, width=self.ir_size, height=self.ir_size)
        self.ir_edges = ogcImage(self.ir_image).Edges(self.canny_min, self.canny_max)
        return

    def OnThresholdChange(self, event):
        # Update edge detection threshold and mark for redraw.
        self.dirty = True
        self.canny_min = event.min_value
        self.canny_max = event.max_value
        self.ir_edges = ogcImage(self.ir_image).Edges(self.canny_min, self.canny_max)
        return

    def OnShowImageChange(self, event):
        # Toggle image display.
        if self.show_image != event.value:
            self.dirty = True
            self.show_image = event.value
        return

    def OnShowContoursChange(self, event):
        # Toggle contour display.
        if self.show_contours != event.value:
            self.dirty = True
            self.show_contours = event.value
        return

    def Draw(self, dc):
        if self.bitmap is not None:
            # Compute offsets to center the image.
            xoff = (self.Size[0] - self.image.width) // 2
            yoff = (self.Size[1] - self.image.height) // 2
            # Draw image if enabled.
            if self.show_image:
                dc.DrawBitmap(self.bitmap, xoff, yoff)

            # Draw contours if enabled.
            if self.show_contours and self.ir_edges.contours:
                # Scale contour points and offset them as needed.
                contours = [
                    c * [
                        self.image.width / self.ir_size,
                        self.image.height / self.ir_size
                    ] + [xoff, yoff]
                    for c in self.ir_edges.contours
                ]
                # Create line segments from contour points.
                lines = np.vstack([
                    np.column_stack([c, np.roll(c, -1, axis=0)])
                    for c in contours
                ]).reshape(-1, 4).astype(int)
                # Draw lines.
                dc.SetPen(wx.Pen((0, 255, 0)))
                dc.DrawLineList(lines.tolist())
                # Draw points.
                points = np.vstack(contours).astype(int)
                dc.SetPen(wx.Pen((255, 0, 0)))
                dc.DrawPointList(points.tolist())

            # Draw bounding box around the image.
            dc.SetBrush(wx.Brush((0, 0, 0), wx.TRANSPARENT))
            dc.SetPen(wx.Pen((255, 0, 255)))
            dc.DrawRectangle(xoff, yoff, self.bitmap.GetWidth(), self.bitmap.GetHeight() - 2)
        return

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
        return

    def OnSize(self, event=None):
        # Mark for redraw when window is resized.
        self.dirty = True
        return

    def OnIdle(self, event):
        # Redraw when idle if necessary.
        if self.dirty:
            self.dirty = False
            self.dc_buffer = wx.Bitmap(*self.Size)
            self.ProcessImage()
            self.Refresh()
            self.Update()
        return

################################################################################################

# Controller for the image editor UI panel
class ogcImageEditorController(wx.Panel):

    def __init__(self, parent, image):
        # Set up layout, controls, and event bindings for the editor panel.
        style = wx.BORDER_NONE
        super(ogcImageEditorController, self).__init__(parent, style=style)
        self.min_size = [150, 480]
        self.SetMinSize(self.min_size)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND))
        box_main = wx.BoxSizer(wx.HORIZONTAL)

        # Left border.
        border = wx.Panel(self, size=(2, -1), style=style)
        border.SetBackgroundColour(wx.Colour(0, 0, 0))
        box_main.Add(border, 0, wx.EXPAND | wx.RIGHT, 2)

        # Main content layout.
        content = wx.Panel(self, style=style)
        box_content = wx.BoxSizer(wx.VERTICAL)

        # IR size dropdown.
        ir_size_label = wx.StaticText(content, label="IR Size:")
        self.ir_size_choices = ["Small (512)", "Medium (1024)", "Large (2048)"]
        self.ir_size_values = {"Small (512)": 512, "Medium (1024)": 1024, "Large (2048)": 2048}
        self.ir_size_ctrl = wx.Choice(content, choices=self.ir_size_choices)
        self.ir_size_ctrl.SetSelection(1)

        # Threshold sliders.
        threshold_min_label = wx.StaticText(content, label="Threshold Min:")
        self.threshold_min_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.threshold_min_slider.SetValue(100)
        self.threshold_min_value = wx.StaticText(content, label="100", size=(30, -1))

        threshold_max_label = wx.StaticText(content, label="Threshold Max:")
        self.threshold_max_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.threshold_max_slider.SetValue(200)
        self.threshold_max_value = wx.StaticText(content, label="200", size=(30, -1))

        box_min_slider = wx.BoxSizer(wx.HORIZONTAL)
        box_min_slider.Add(self.threshold_min_slider, 1, wx.EXPAND | wx.RIGHT, 1)
        box_min_slider.Add(self.threshold_min_value, 0, wx.ALIGN_CENTER_VERTICAL)

        box_max_slider = wx.BoxSizer(wx.HORIZONTAL)
        box_max_slider.Add(self.threshold_max_slider, 1, wx.EXPAND | wx.RIGHT, 1)
        box_max_slider.Add(self.threshold_max_value, 0, wx.ALIGN_CENTER_VERTICAL)

        # Checkboxes.
        self.show_image_checkbox = wx.CheckBox(content, label="Show Image")
        self.show_contours_checkbox = wx.CheckBox(content, label="Show Contours")
        self.show_image_checkbox.SetValue(True)
        self.show_contours_checkbox.SetValue(True)

        # Layout order.
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

        # Bind events.
        self.ir_size_ctrl.Bind(wx.EVT_CHOICE, self.OnIRSizeChange)
        self.threshold_min_slider.Bind(wx.EVT_SLIDER, self.OnThresholdChange)
        self.threshold_max_slider.Bind(wx.EVT_SLIDER, self.OnThresholdChange)
        self.show_image_checkbox.Bind(wx.EVT_CHECKBOX, self.OnShowImageChange)
        self.show_contours_checkbox.Bind(wx.EVT_CHECKBOX, self.OnShowContoursChange)

        self.Show(True)
        return

    def OnIRSizeChange(self, event):
        # Notify parent that IR size is changed.
        selection = self.ir_size_ctrl.GetStringSelection()
        ir_size_value = self.ir_size_values.get(selection, 1024)
        ir_size_event = IRSizeEvent(value=ir_size_value)
        wx.PostEvent(self.Parent, ir_size_event)
        return

    def OnThresholdChange(self, event):
        # Update min and max threshold values, ensuring min < max.
        min_value = self.threshold_min_slider.GetValue()
        max_value = self.threshold_max_slider.GetValue()
        if min_value >= max_value:
            if event.EventObject == self.threshold_min_slider:
                max_value = min(255, min_value + 1)
                self.threshold_max_slider.SetValue(max_value)
            else:
                min_value = max(0, max_value - 1)
                self.threshold_min_slider.SetValue(min_value)
        self.threshold_min_value.SetLabel(str(min_value))
        self.threshold_max_value.SetLabel(str(max_value))
        threshold_event = ThresholdEvent(min_value=min_value, max_value=max_value)
        wx.PostEvent(self.Parent, threshold_event)
        return

    def OnShowImageChange(self, event):
        # Notify parent when show image checkbox is toggled.
        show_image_value = self.show_image_checkbox.GetValue()
        show_image_event = ShowImageEvent(value=show_image_value)
        wx.PostEvent(self.Parent, show_image_event)
        return

    def OnShowContoursChange(self, event):
        # Notify parent when show contours checkbox is toggled.
        show_contours_value = self.show_contours_checkbox.GetValue()
        show_contours_event = ShowContoursEvent(value=show_contours_value)
        wx.PostEvent(self.Parent, show_contours_event)
        return

################################################################################################

class ogcImageEditorPanel(wx.Panel):

    def __init__(self, parent, image):
        # Initialize the panel with border and character input support.
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcImageEditorPanel, self).__init__(parent, style=style)
        # Set the image and panel background color.
        self.image = image
        self.SetBackgroundColour((0, 0, 0))
        # Create and set up the main layout (viewer and controller).
        box_main = wx.BoxSizer(wx.HORIZONTAL)
        self.viewer = ogcImageEditorViewer(self, self.image)
        box_main.Add(self.viewer, 1, wx.EXPAND)
        # Create and add the controller panel.
        box_controller = wx.BoxSizer(wx.VERTICAL)
        self.controller = ogcImageEditorController(self, self.image)
        box_controller.Add(self.controller, 1, wx.EXPAND)
        box_main.Add(box_controller, 0, wx.EXPAND)
        # Apply the layout.
        self.SetSizerAndFit(box_main)
        # Bind custom events to the appropriate handler methods.
        self.Bind(EVT_THRESHOLD, self.OnThresholdChange)
        self.Bind(EVT_IR_SIZE, self.OnIRSizeChange)
        self.Bind(EVT_SHOW_IMAGE, self.OnShowImageChange)
        self.Bind(EVT_SHOW_CONTOURS, self.OnShowContoursChange)
        # Display the panel.
        self.Show(True)
        return

    def OnThresholdChange(self, event):
        # Forward threshold event to the viewer.
        viewer_event = ThresholdEvent(min_value=event.min_value, max_value=event.max_value)
        wx.PostEvent(self.viewer, viewer_event)
        return

    def OnIRSizeChange(self, event):
        # Forward IR size event to the viewer.
        viewer_event = IRSizeEvent(value=event.value)
        wx.PostEvent(self.viewer, viewer_event)
        return

    def OnShowImageChange(self, event):
        # Forward show image event to the viewer.
        show_image_event = ShowImageEvent(value=event.value)
        wx.PostEvent(self.viewer, show_image_event)
        return

    def OnShowContoursChange(self, event):
        # Forward show contours event to the viewer.
        show_contours_event = ShowContoursEvent(value=event.value)
        wx.PostEvent(self.viewer, show_contours_event)
        return

################################################################################################
