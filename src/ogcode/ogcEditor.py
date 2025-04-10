################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the image editor.
'''
################################################################################################

import wx
import numpy as np
from time import sleep
from threading import Thread, Lock

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcSettings import ogcSettings
from .ogcImage import ogcImage
from .ogcGCode import gcScript
from .ogcVector import flip_lines, rotate_lines

################################################################################################

# Viewer modes.
from enum import Enum
class ViewerMode(Enum):
    IMAGE = 1
    GCODE = 2

# Tool IDs.
class EditorTool():
    ROT_CLOCK   = wx.NewIdRef()
    ROT_ACLOCK  = wx.NewIdRef()
    FLIP_H      = wx.NewIdRef()
    FLIP_V      = wx.NewIdRef()
    ZOOM_IN     = wx.NewIdRef()
    ZOOM_DEF    = wx.NewIdRef()
    ZOOM_OUT    = wx.NewIdRef()

################################################################################################

class ogcEditorViewer(wx.Panel):
    def __init__(self, parent, data, path, mode):
        # Initialize panel.
        style = wx.BORDER_NONE | wx.WANTS_CHARS
        super().__init__(parent, style=style)
        self.min_size = (640, 480)
        self.SetMinSize(self.min_size)
        # Initialize data depending on mode.
        self.mode = mode
        self.data = data
        self.path = path
        self.ir_size = 1024
        self.gcode_size = ogcSettings.Get("gcode_size")
        if self.mode == ViewerMode.IMAGE:
            self.gcode = None
            self.laser_power = 16
            self.orig_image = ogcImage(self.data).Cleanup()
            self.ir_image = ogcImage(self.orig_image, width=self.ir_size, height=self.ir_size)
            self.canny_min = 100
            self.canny_max = 200
            self.ir_edges = ogcImage(self.ir_image).Edges(self.canny_min, self.canny_max)
            self.lines = self.ir_edges.lines
        elif self.mode == ViewerMode.GCODE:
            self.gcode = self.data
            self.laser_power = self.gcode.get_laser_power()
            self.lines = self.gcode.to_lines(self.ir_size)
            min_dim = min(self.min_size)
            self.lines_scale = np.array([min_dim / self.ir_size, min_dim / self.ir_size])

        # Rendering and view state.
        self.image_bitmap = None
        self.canvas_bitmap = None
        self.color_fg = ogcSettings.Get("editor_fgcolor")
        self.color_bg = ogcSettings.Get("editor_bgcolor")
        self.dirty = True
        self.show_image = True
        self.show_lines = True

        # Zoom and pan support.
        self.zoom = 1.0
        self.offset = np.array([0, 0], dtype=float)
        self.drag_start = None
        self.recenter_on_next_render = True

        # Bind events.
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_RIGHT_UP, self.OnRightUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(ogcEvents.EVT_THRESHOLD, self.OnThreshold)
        self.Bind(ogcEvents.EVT_IR_SIZE, self.OnIRSize)
        self.Bind(ogcEvents.EVT_SHOW_IMAGE, self.OnShowImage)
        self.Bind(ogcEvents.EVT_SHOW_LINES, self.OnShowLines)
        self.Bind(ogcEvents.EVT_LASER_POWER, self.OnLaserPower)

        wx.CallAfter(self.OnSize)
        return

    def GetGCode(self):
        # Update G-Code.
        if self.mode == ViewerMode.IMAGE:
            size_in = (self.image.width, self.image.height)
        elif self.mode == ViewerMode.GCODE:
            size_in = (self.ir_size, self.ir_size)
        self.gcode = gcScript(
            lines=self.lines,
            laser_power=self.laser_power,
            size_in=size_in,
            size_out=(self.gcode_size, self.gcode_size)
        )
        return self.gcode

    def Zoom(self, factor, pos = None):
        # Zoom in/out centered on a position with multiplicative scaling.
        new_zoom = max(0.1, min(self.zoom * factor, 32.0))

        if not np.isclose(new_zoom, self.zoom):
            if pos is None:
                pos = np.array([self.Size[0]/2, self.Size[1]/2])
            image_pos = (pos - self.offset) / self.zoom
            self.zoom = new_zoom
            self.offset = pos - image_pos * self.zoom
            self.dirty = True
        return

    def ZoomIn(self, pos = None):
        # Zoom it at postion pos.
        self.Zoom(1.1, pos)
        return

    def ZoomOut(self, pos = None):
        # Zoom out at postion pos.
        self.Zoom(1.0 / 1.1, pos)
        return

    def ZoomDef(self, pos = None):
        # Restore default zoom and recenter.
        self.zoom = 1.0
        self.recenter_on_next_render = True
        self.dirty = True
        return

    def OnMouseWheel(self, event):
        # Zoom in/out centered on the mouse position.
        if event.GetWheelRotation() > 0:
            mouse_pos = np.array(event.GetPosition())
            self.ZoomIn(mouse_pos)
        else:
            mouse_pos = np.array(event.GetPosition())
            self.ZoomOut(mouse_pos)
        return

    def OnRightDown(self, event):
        # Begin dragging for panning.
        self.drag_start = np.array(event.GetPosition())
        self.CaptureMouse()
        return

    def OnRightUp(self, event):
        # End dragging.
        if self.HasCapture():
            self.ReleaseMouse()
        if self.drag_start is not None:
            self.drag_start = None
            self.dirty = True
        return

    def OnMouseMove(self, event):
        # Handle panning motion.
        if event.Dragging() and event.RightIsDown() and self.drag_start is not None:
            pos = np.array(event.GetPosition())
            delta = pos - self.drag_start
            self.offset += delta
            self.drag_start = pos
            self.dirty = True
        return

    def ProcessImage(self):
        # Resize image and regenerate bitmap.
        self.image = ogcImage(self.ir_image)
        # Debug view of the raster image used to simplify lines.
        #self.image = ogcImage(self.ir_edges)
        dims = (self.Size[0], None) if self.Size[0] < self.Size[1] else (None, self.Size[1])
        self.image.Resize(*dims)
        self.image_bitmap = wx.Bitmap(self.image.WXImage())
        return

    def OnIRSize(self, event):
        # Update intermediate image resolution and edge detection.
        self.dirty = True
        self.recenter_on_next_render = True
        self.ir_size = event.value
        self.ir_image = ogcImage(self.orig_image, width=self.ir_size, height=self.ir_size)
        self.ir_edges = ogcImage(self.ir_image).Edges(self.canny_min, self.canny_max)
        self.lines = self.ir_edges.lines
        return

    def OnThreshold(self, event):
        # Update edge detection thresholds.
        self.dirty = True
        self.canny_min = event.min_value
        self.canny_max = event.max_value
        self.ir_edges = ogcImage(self.ir_image).Edges(self.canny_min, self.canny_max)
        self.lines = self.ir_edges.lines
        return

    def OnShowImage(self, event):
        # Toggle image visibility.
        if self.show_image != event.value:
            self.dirty = True
            self.show_image = event.value
        return

    def OnShowLines(self, event):
        # Toggle line overlay visibility.
        if self.show_lines != event.value:
            self.dirty = True
            self.show_lines = event.value
        return

    def OnLaserPower(self, event):
        # Set laser power.
        self.laser_power = event.value
        return

    def OnPaint(self, event):
        # Avoid drawing too early.
        if self.Size[0] <= 0 or self.Size[1] <= 0:
            return

        # Clear background.
        dc = wx.BufferedPaintDC(self)
        dc.SetBrush(wx.Brush(self.color_bg))
        dc.SetPen(wx.Pen(self.color_bg))
        dc.DrawRectangle(0, 0, self.Size[0], self.Size[1])

        # If no redraw needed, draw cached bitmap and return.
        if self.canvas_bitmap is not None and not self.dirty:
            dc.DrawBitmap(self.canvas_bitmap, 0, 0, True)
            return

        # Recompute cached bitmap.
        self.canvas_bitmap = wx.Bitmap(self.Size[0], self.Size[1])
        mem_dc = wx.MemoryDC(self.canvas_bitmap)
        gc = wx.GraphicsContext.Create(mem_dc)

        # Change rendering based on mode.
        if self.mode == ViewerMode.IMAGE:
            if self.image_bitmap is None:
                return
            if self.show_image:
                # Draw the image bitmap with a GC so it can be scaled easily.
                gc.PushState()
                gc.Translate(*self.offset)
                gc.Scale(self.zoom, self.zoom)
                gc.DrawBitmap(
                    self.image_bitmap,
                    0, 0,
                    self.image_bitmap.GetWidth(),
                    self.image_bitmap.GetHeight()
                )
                gc.PopState()
            # Compute scaling for lines / points.
            scale = np.array([self.image.width / self.ir_size,
                              self.image.height / self.ir_size]) * self.zoom
        elif self.mode == ViewerMode.GCODE:
            # Compute scaling for lines / points.
            scale = self.lines_scale * self.zoom

        # This correction is here to deal with some difference between the
        # GC scaling vs the manual scaling with the points / lines and the DC.
        # It seems to need to change based on the zoom level to line up perfectly.
        offset_correction = np.array([1.5, 1.5]) * (self.zoom / 2.0)
        offset = self.offset + offset_correction

        # Draw lines / points if needed.
        if self.show_lines and self.lines.size > 0:
            scaled_lines = np.round(self.lines * scale + offset).astype(int)
            mem_dc.SetPen(wx.Pen((0, 255, 0)))
            mem_dc.DrawLineList(scaled_lines.reshape(-1, 4).tolist())
            mem_dc.SetPen(wx.Pen((255, 0, 0)))
            mem_dc.DrawPointList(scaled_lines.reshape(-1, 2).tolist())

        # Draw bounding box for IR size in purple.
        bounding_box = np.array([
            [-1, -1], [self.ir_size, -1],
            [self.ir_size+1, self.ir_size+1], [-1, self.ir_size+1],
            [-1, -1]
        ])
        scaled_box = np.round(bounding_box * scale + offset).astype(int)
        mem_dc.SetPen(wx.Pen((64, 0, 128)))
        mem_dc.DrawLines(scaled_box.tolist())

        # Draw the updated cached bitmap.
        mem_dc.SelectObject(wx.NullBitmap)
        dc.DrawBitmap(self.canvas_bitmap, 0, 0, True)
        return

    def OnSize(self, event=None):
        # Triggered when the widget is resized.
        self.dirty = True
        self.recenter_on_next_render = True
        return

    def OnIdle(self, event):
        # Reprocess / redraw if needed.
        if self.dirty:
            if self.mode == ViewerMode.IMAGE:
                self.ProcessImage()
                # Center image if requested.
                if self.recenter_on_next_render:
                    self.zoom = 1.0
                    self.offset = np.array([
                        (self.Size[0] - self.image_bitmap.GetWidth()) / 2,
                        (self.Size[1] - self.image_bitmap.GetHeight()) / 2
                    ])
            elif self.mode == ViewerMode.GCODE:
                # Center G-Code if requested.
                if self.recenter_on_next_render:
                    self.zoom = 1.0
                    min_dim = min(self.Size)
                    self.lines_scale = np.array([
                        min_dim / self.ir_size * 0.925, min_dim / self.ir_size * 0.925
                    ])
                    self.offset = np.array([
                        (self.Size[0] - self.ir_size * self.lines_scale[0]) / 2,
                        (self.Size[1] - self.ir_size * self.lines_scale[0]) / 2
                    ])
            self.Refresh()
            self.Update()
            self.recenter_on_next_render = False
            self.dirty = False
        return

    def ToolCommand(self, command):
        if command == EditorTool.ROT_CLOCK:
            # Rotate clockwise.
            if self.mode == ViewerMode.IMAGE:
                self.orig_image.Rotate(clockwise=True)
                self.ir_image.Rotate(clockwise=True)
                self.ir_edges.Rotate(clockwise=True)
                self.lines = self.ir_edges.lines
            elif self.mode == ViewerMode.GCODE:
                self.lines = rotate_lines(
                    self.lines,
                    width=self.ir_size,
                    height=self.ir_size,
                    clockwise=True
                )
            self.dirty = True
        elif command == EditorTool.ROT_ACLOCK:
            # Rotate anti-clockwise.
            if self.mode == ViewerMode.IMAGE:
                self.orig_image.Rotate(clockwise=False)
                self.ir_image.Rotate(clockwise=False)
                self.ir_edges.Rotate(clockwise=False)
                self.lines = self.ir_edges.lines
            elif self.mode == ViewerMode.GCODE:
                self.lines = rotate_lines(
                    self.lines,
                    width=self.ir_size,
                    height=self.ir_size,
                    clockwise=False
                )
            self.dirty = True
        elif command == EditorTool.FLIP_H:
            # Flip horizontal.
            if self.mode == ViewerMode.IMAGE:
                self.orig_image.Flip(vertical=False)
                self.ir_image.Flip(vertical=False)
                self.ir_edges.Flip(vertical=False)
                self.lines = self.ir_edges.lines
            elif self.mode == ViewerMode.GCODE:
                self.lines = flip_lines(
                    self.lines,
                    width=self.ir_size,
                    height=self.ir_size,
                    vertical=False
                )
            self.dirty = True
        elif command == EditorTool.FLIP_V:
            # Flip vertical.
            if self.mode == ViewerMode.IMAGE:
                self.orig_image.Flip(vertical=True)
                self.ir_image.Flip(vertical=True)
                self.ir_edges.Flip(vertical=True)
                self.lines = self.ir_edges.lines
            elif self.mode == ViewerMode.GCODE:
                self.lines = flip_lines(
                    self.lines,
                    width=self.ir_size,
                    height=self.ir_size,
                    vertical=True
                )
            self.dirty = True
        elif command == EditorTool.ZOOM_IN:
            # Zoom in.
            self.ZoomIn()
            pass
        elif command == EditorTool.ZOOM_DEF:
            # Zoom in.
            self.ZoomDef()
            pass
        elif command == EditorTool.ZOOM_OUT:
            # Zoom out.
            self.ZoomOut()
            pass
        else:
            print(f"Viewer: Unknown command {command}.")
        return

################################################################################################

# Controller for the image editor UI panel.
class ogcEditorController(wx.Panel):

    def __init__(self, parent, mode):
        # Set up layout, controls, and event bindings for the editor panel.
        style = wx.BORDER_NONE
        super(ogcEditorController, self).__init__(parent, style=style)
        self.min_size = [164, 480]
        self.SetMinSize(self.min_size)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND))
        self.mode = mode
        box_main = wx.BoxSizer(wx.HORIZONTAL)

        # Left border.
        border = wx.Panel(self, style=style)
        border.SetMinSize((2, 1))
        border.SetBackgroundColour(wx.Colour(0, 0, 0))
        box_main.Add(border, 0, wx.EXPAND | wx.RIGHT, 2)

        # Main content layout.
        content = wx.Panel(self, style=style)
        content.SetMinSize((64, 64))
        box_content = wx.BoxSizer(wx.VERTICAL)

        if self.mode == ViewerMode.IMAGE:
            # IR size dropdown.
            ir_size_label = wx.StaticText(content, label="IR Size:")
            self.ir_size_choices = ["Small (512)", "Medium (1024)", "Large (2048)"]
            self.ir_size_values = {"Small (512)": 512, "Medium (1024)": 1024, "Large (2048)": 2048}
            self.ir_size_ctrl = wx.Choice(content, choices=self.ir_size_choices)
            self.ir_size_ctrl.SetSelection(1)

            # Threshold sliders.
            threshold_min_label = wx.StaticText(content, label="Edge Threshold Min:")
            self.threshold_min_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
            self.threshold_min_slider.SetValue(100)
            self.threshold_min_value = wx.StaticText(content, label="100")
            self.threshold_min_value.SetMinSize((32, -1))

            threshold_max_label = wx.StaticText(content, label="Edge Threshold Max:")
            self.threshold_max_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
            self.threshold_max_slider.SetValue(200)
            self.threshold_max_value = wx.StaticText(content, label="200")
            self.threshold_max_value.SetMinSize((32, -1))

            box_min_slider = wx.BoxSizer(wx.HORIZONTAL)
            box_min_slider.Add(self.threshold_min_slider, 1, wx.EXPAND | wx.RIGHT, 1)
            box_min_slider.Add(self.threshold_min_value, 0, wx.ALIGN_CENTER_VERTICAL)

            box_max_slider = wx.BoxSizer(wx.HORIZONTAL)
            box_max_slider.Add(self.threshold_max_slider, 1, wx.EXPAND | wx.RIGHT, 1)
            box_max_slider.Add(self.threshold_max_value, 0, wx.ALIGN_CENTER_VERTICAL)

            # Checkboxes.
            self.show_image_checkbox = wx.CheckBox(content, label="Show Image")
            self.show_lines_checkbox = wx.CheckBox(content, label="Show Lines")
            self.show_image_checkbox.SetValue(True)
            self.show_lines_checkbox.SetValue(True)

            # Layout order for image mode.
            box_content.Add(ir_size_label, 0, wx.LEFT | wx.TOP, 2)
            box_content.Add(self.ir_size_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
            box_content.AddSpacer(6)
            box_content.Add(threshold_min_label, 0, wx.LEFT | wx.TOP, 2)
            box_content.Add(box_min_slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)
            box_content.Add(threshold_max_label, 0, wx.LEFT | wx.TOP, 0)
            box_content.Add(box_max_slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 2)

        # Laser power slider (shared by both modes).
        laser_power_label = wx.StaticText(content, label="Laser Power:")
        self.laser_power_slider = wx.Slider(content, minValue=0, maxValue=255, style=wx.SL_HORIZONTAL)
        self.laser_power_slider.SetValue(16)
        self.laser_power_value = wx.StaticText(content, label="16")
        self.laser_power_value.SetMinSize((32, -1))

        box_laser_slider = wx.BoxSizer(wx.HORIZONTAL)
        box_laser_slider.Add(self.laser_power_slider, 1, wx.EXPAND | wx.RIGHT, 1)
        box_laser_slider.Add(self.laser_power_value, 0, wx.ALIGN_CENTER_VERTICAL)

        box_content.Add(laser_power_label, 0, wx.LEFT | wx.TOP, 2)
        box_content.Add(box_laser_slider, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 1)

        if self.mode == ViewerMode.IMAGE:
            box_content.Add(self.show_image_checkbox, 0, wx.LEFT | wx.TOP, 2)
            box_content.Add(self.show_lines_checkbox, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 2)

        content.SetSizerAndFit(box_content)
        box_main.Add(content, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)

        # Bind events.
        if self.mode == ViewerMode.IMAGE:
            self.ir_size_ctrl.Bind(wx.EVT_CHOICE, self.OnIRSize)
            self.threshold_min_slider.Bind(wx.EVT_SLIDER, self.OnThreshold)
            self.threshold_max_slider.Bind(wx.EVT_SLIDER, self.OnThreshold)
            self.show_image_checkbox.Bind(wx.EVT_CHECKBOX, self.OnShowImage)
            self.show_lines_checkbox.Bind(wx.EVT_CHECKBOX, self.OnShowLines)

        self.laser_power_slider.Bind(wx.EVT_SLIDER, self.OnLaserPower)

        self.Show(True)
        return

    def OnIRSize(self, event):
        # Notify parent that IR size is changed.
        selection = self.ir_size_ctrl.GetStringSelection()
        ir_size_value = self.ir_size_values.get(selection, 1024)
        ir_size_event = ogcEvents.IRSize(value=ir_size_value)
        wx.PostEvent(self.Parent, ir_size_event)
        return

    def OnThreshold(self, event):
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
        threshold_event = ogcEvents.Threshold(min_value=min_value, max_value=max_value)
        wx.PostEvent(self.Parent, threshold_event)
        return

    def OnLaserPower(self, event):
        # Notify parent when laser power slider is adjusted.
        power_value = self.laser_power_slider.GetValue()
        self.laser_power_value.SetLabel(str(power_value))
        power_event = ogcEvents.LaserPower(value=power_value)
        wx.PostEvent(self.Parent, power_event)
        return

    def OnShowImage(self, event):
        # Notify parent when show image checkbox is toggled.
        show_image_value = self.show_image_checkbox.GetValue()
        show_image_event = ogcEvents.ShowImage(value=show_image_value)
        wx.PostEvent(self.Parent, show_image_event)
        return

    def OnShowLines(self, event):
        # Notify parent when show lines checkbox is toggled.
        show_lines_value = self.show_lines_checkbox.GetValue()
        show_lines_event = ogcEvents.ShowLines(value=show_lines_value)
        wx.PostEvent(self.Parent, show_lines_event)
        return

################################################################################################

class ogcEditorPanel(wx.Panel):

    def __init__(self, parent, data, path, mode):
        # Initialize the panel with border and character input support.
        style = wx.BORDER_NONE | wx.WANTS_CHARS
        super(ogcEditorPanel, self).__init__(parent, style=style)
        self.SetMinSize((640, 480))
        self.SetBackgroundColour((0, 0, 0))
        # Create an image if passed image data, else use G-Code.
        self.data = data
        self.path = path
        self.mode = mode
        # Create and set up the main layout (viewer and controller).
        box_main = wx.BoxSizer(wx.HORIZONTAL)
        self.viewer = ogcEditorViewer(self, self.data, self.path, self.mode)
        box_main.Add(self.viewer, 1, wx.EXPAND)
        # Create and add the controller panel.
        box_controller = wx.BoxSizer(wx.VERTICAL)
        self.controller = ogcEditorController(self, self.mode)
        box_controller.Add(self.controller, 1, wx.EXPAND)
        box_main.Add(box_controller, 0, wx.EXPAND)
        # Apply the layout.
        self.SetSizerAndFit(box_main)
        # Bind custom events to the appropriate handler methods.
        self.Bind(ogcEvents.EVT_THRESHOLD, self.OnThreshold)
        self.Bind(ogcEvents.EVT_IR_SIZE, self.OnIRSize)
        self.Bind(ogcEvents.EVT_SHOW_IMAGE, self.OnShowImage)
        self.Bind(ogcEvents.EVT_SHOW_LINES, self.OnShowLines)
        self.Bind(ogcEvents.EVT_LASER_POWER, self.OnLaserPower)
        # Display the panel.
        self.Show(True)
        return

    def OnThreshold(self, event):
        # Forward threshold event to the viewer.
        viewer_event = ogcEvents.Threshold(min_value=event.min_value, max_value=event.max_value)
        wx.PostEvent(self.viewer, viewer_event)
        return

    def OnIRSize(self, event):
        # Forward IR size event to the viewer.
        viewer_event = ogcEvents.IRSize(value=event.value)
        wx.PostEvent(self.viewer, viewer_event)
        return

    def OnShowImage(self, event):
        # Forward show image event to the viewer.
        show_image_event = ogcEvents.ShowImage(value=event.value)
        wx.PostEvent(self.viewer, show_image_event)
        return

    def OnShowLines(self, event):
        # Forward show lines event to the viewer.
        show_lines_event = ogcEvents.ShowLines(value=event.value)
        wx.PostEvent(self.viewer, show_lines_event)
        return

    def OnLaserPower(self, event):
        # Forward laser power event to the viewer.
        laser_power_event = ogcEvents.LaserPower(value=event.value)
        wx.PostEvent(self.viewer, laser_power_event)
        return

    def GetGCode(self):
        # Return this editor's gcode.
        return self.viewer.GetGCode()

    def ToolCommand(self, command):
        # Pass along a command from toolbar.
        self.viewer.ToolCommand(command)
        return

    def MarkDirty(self):
        # Mark viewer as dirty to force full redraw.
        self.viewer.dirty = True
        return

################################################################################################
