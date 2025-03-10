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

    def SerialPortErrorMessage(self, port_index : int):
        error_string = "\n".join( (f"[{error}]" for error in self.serial.error) )
        message = f"Error(s):\n{error_string}\n\n"
        message += f"Serial Port:\n{self.port_strings[port_index]}"
        caption = "Error Engraving"
        dlg = wx.MessageDialog(self, message, caption, wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        return

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        # Main sizer.
        box_main = wx.BoxSizer(wx.VERTICAL)
        # Serial port list.
        st_names = wx.StaticText(self, -1, "Serial Port:")
        self.cb_ports = wx.ComboBox(self, size=(640, -1), style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.OnSelectSerial)
        box_list = wx.BoxSizer(wx.VERTICAL)
        box_list.Add(st_names, 0, wx.ALL, 5)
        box_list.Add(self.cb_ports, 0, wx.ALL, 5)
        box_main.Add(box_list)
        # Controls.
        btn_engrave = wx.Button(self, wx.ID_ANY, "Engrave")
        btn_engrave.Bind(wx.EVT_BUTTON, self.OnEngrave)
        btn_engrave.SetBitmap(ogcIcons.Get('tick'))
        btn_cancel = wx.Button(self, wx.ID_ANY, "Cancel")
        btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        btn_cancel.SetBitmap(ogcIcons.Get('cross'))
        box_ctrl = wx.BoxSizer(wx.HORIZONTAL)
        box_ctrl.Add(btn_cancel, 0, wx.EXPAND)
        box_ctrl.Add(btn_engrave, 0, wx.EXPAND)
        box_main.Add(box_ctrl, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        # Fit.
        self.SetSizerAndFit(box_main)
        self.Layout()
        self.cb_ports.SetSelection(wx.NOT_FOUND)
        self.Show(True)
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
                self.SerialPortErrorMessage(self.port_index)
        # Catch close event.
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        return

    def OnSelectSerial(self, event):
        # Open selected serial port.
        self.port_index = event.GetSelection()
        port = self.ports[self.port_strings[self.port_index]][0]
        if self.serial:
            self.serial.close()
        self.serial = ogcSerialDriver(port)
        if self.serial.error:
            self.SerialPortErrorMessage(self.port_index)
        return

    def OnEngrave(self, event):
        # Write G-Code data to serial port.
        test_gcode = """G90
G20
G17 G64 P0.001
M3 S16
F2.00
G0 Z0.2500
G0 X-126.4004 Y239.6813
G1 Z-0.0050
G1 X-126.4004 Y239.6813
G1 X-126.1612 Y239.5639
G1 X-125.9311 Y239.4294
G1 X-222.2960 Y37.9260
G0 Z0.2500
M5
M2
"""
        self.serial.write(test_gcode)
        if self.serial.error:
            self.SerialPortErrorMessage(self.port_index)
        return

    def OnCancel(self, event):
        self.OnClose()
        return

    def OnClose(self, event=None):
        if self.serial:
            self.serial.close()
            self.serial = None
        if not self.Parent.closing:
            self.Parent.OnClose()
        return


################################################################################################
class ogcEngraveFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Engrave", size=(800,600),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        icon = wx.Icon()
        icon.CopyFromBitmap(ogcIcons.Get('page_go'))
        self.SetIcon(icon)
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.engrave_panel = ogcEngravePanel(self)
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
