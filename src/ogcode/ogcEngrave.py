################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for engraveing G-code to a microcontroller over a serial port.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcSerialDriver import ogcSerialDriver


################################################################################################
class ogcEngravePanel(wx.Panel):

    def UpdateMessages(self):
        message = ""
        error_string = ""
        if self.serial:
            error_string = "\n".join([f"[{error}]" for error in self.serial.error])
        if error_string:
            message += f"Error(s):\n{error_string}"
        self.tc_messages.SetValue(message)
        return

    def __init__(self, parent, gcode):
        wx.Panel.__init__(self, parent, -1)
        self.gcode = gcode
        # Main sizer.
        box_main = wx.BoxSizer(wx.VERTICAL)
        # Serial port list.
        st_serial_port = wx.StaticText(self, -1, "Serial Port:")
        self.cb_ports = wx.ComboBox(self, size=(640, -1), style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectSerial)
        box_serial_port = wx.BoxSizer(wx.VERTICAL)
        box_serial_port.Add(st_serial_port, 0, wx.ALL, 5)
        box_serial_port.Add(self.cb_ports, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box_main.Add(box_serial_port)
        # Progress bar.
        self.st_progress = wx.StaticText(self, -1, "Engrave Progress: 0%")
        progress_style = style=wx.GA_SMOOTH | wx.GA_HORIZONTAL | wx.GA_TEXT
        self.g_progress = wx.Gauge(self, size=(640, 32), style=progress_style)
        box_progress = wx.BoxSizer(wx.VERTICAL)
        box_progress.Add(self.st_progress, 0, wx.ALL, 5)
        box_progress.Add(self.g_progress, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box_main.Add(box_progress)
        # Messages / errors.
        st_messages = wx.StaticText(self, -1, "Messages:")
        self.tc_messages = wx.TextCtrl(self, size=(640, 96), style=wx.TE_READONLY | wx.TE_MULTILINE)
        box_messages = wx.BoxSizer(wx.VERTICAL)
        box_messages.Add(st_messages, 0, wx.ALL, 5)
        box_messages.Add(self.tc_messages, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        box_main.Add(box_messages)
        # Controls.
        self.btn_engrave = wx.Button(self, wx.ID_ANY, "Engrave")
        self.btn_engrave.Bind(wx.EVT_BUTTON, self.OnEngrave)
        self.btn_engrave.SetBitmap(ogcIcons.Get('tick'))
        btn_close = wx.Button(self, wx.ID_ANY, "Close")
        btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
        btn_close.SetBitmap(ogcIcons.Get('cross'))
        btn_close.Bind(wx.EVT_BUTTON, self.OnClose)
        self.btn_stop = wx.Button(self, wx.ID_ANY, "Stop")
        self.btn_stop.Bind(wx.EVT_BUTTON, self.OnStop)
        self.btn_stop.SetBitmap(ogcIcons.Get('stop'))
        box_ctrl = wx.BoxSizer(wx.HORIZONTAL)
        box_ctrl.Add(btn_close, 0, wx.EXPAND)
        box_ctrl.Add(self.btn_stop, 0, wx.EXPAND)
        box_ctrl.Add(self.btn_engrave, 0, wx.EXPAND)
        box_main.AddSpacer(10)
        box_main.Add(box_ctrl, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        # Collect serial ports, ordered by longest description first.
        ports_list = ogcSerialDriver.get_ports()
        ports_list.sort(key=lambda p: len(p[2]), reverse=True)
        self.port_strings = []
        self.ports = {}
        for port, desc, hwid in ports_list:
            port_string = f"{port}: - "
            port_string += f"'{desc}'" if desc != "n/a" else "?"
            port_string += f" - '{hwid}'" if hwid != "n/a" else ""
            self.port_strings.append(port_string)
            self.ports[port_string] = (port, desc, hwid)
        self.cb_ports.SetItems(self.port_strings)
        # Default to first serial port.
        self.cb_ports.SetSelection(0)
        self.serial = None
        if len(ports_list) > 0:
            self.port_index = 0
            self.serial = ogcSerialDriver(ports_list[self.port_index][0])
            if self.serial.error:
                self.UpdateMessages()
        # Fit.
        self.SetSizerAndFit(box_main)
        self.Layout()
        self.cb_ports.SetSelection(wx.NOT_FOUND)
        self.Show(True)
        # Create a timer to poll status / progress of serial driver.
        self.progress = 0
        self.serial_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnSerialTimer, self.serial_timer)
        self.serial_timer.Start(100)
        # Catch close event.
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        return

    def OnSelectSerial(self, event):
        # Don't switch serial port if current one is not finished.
        if self.serial and not self.serial.finished:
            self.cb_ports.SetSelection(self.port_index)
            return
        # Open selected serial port.
        self.port_index = event.GetSelection()
        port = self.ports[self.port_strings[self.port_index]][0]
        if self.serial:
            self.serial.close()
        self.serial = ogcSerialDriver(port)
        if self.serial.error:
            self.UpdateMessages()
        return

    def OnSerialTimer(self, event):
        # Update engrave and stop button enabled states.
        if not self.serial or self.serial.finished:
            self.btn_engrave.Enable()
            self.btn_stop.Disable()
        # Update progress bar.
        progress = int(self.serial.progress) if self.serial else 0
        if progress != self.progress:
            self.progress = progress
            self.g_progress.SetValue(int(self.progress))
            self.st_progress.SetLabel(f"Engrave Progress: {self.progress}%")
        # Update messages.
        self.UpdateMessages()
        return

    def OnEngrave(self, event):
        # Don't start engraving if already in progress.
        if self.serial and not self.serial.finished:
            return
        # Disable the engrave and stop buttons as well as reset progress bar.
        self.g_progress.SetValue(0)
        self.btn_engrave.Disable()
        self.btn_stop.Enable()
        # Write G-Code data to serial port.
        self.serial.write(str(self.gcode))
        if self.serial.error:
            self.UpdateMessages()
        return

    def OnStop(self, event):
        # Stop engraving.
        if self.serial:
            self.serial.stop()
        return

    def OnClose(self, event=None):
        # Close the engrave dialog.
        if self.serial:
            self.serial.close()
            self.serial = None
        if not self.Parent.closing:
            self.Parent.OnClose()
        return


################################################################################################
class ogcEngraveFrame(wx.Frame):
    def __init__(self, parent, gcode):
        wx.Frame.__init__(self, parent, title="Engrave", size=(800,600),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        self.gcode = gcode
        icon = wx.Icon()
        icon.CopyFromBitmap(ogcIcons.Get('page_go'))
        self.SetIcon(icon)
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.engrave_panel = ogcEngravePanel(self, gcode)
        box_main.Add(self.engrave_panel)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.closing = False
        return

    def OnClose(self, event=None):
        self.closing = True
        self.engrave_panel.OnClose()
        self.Parent.engrave_frame = None
        self.Destroy()
        return

################################################################################################
