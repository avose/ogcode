################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for uploading G-code to a microcontroller over a serial port.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcSerialDriver import ogcSerialDriver

from string import ascii_lowercase as ascii_lc


################################################################################################
class ogcUploadPanel(wx.Panel):
    
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        # Main sizer.
        box_main = wx.BoxSizer(wx.VERTICAL)
        # Serial port list.
        st_names = wx.StaticText(self, -1, "Serial Ports:")
        self.lb_ports = wx.ListBox(self, -1, size=(480, 240))
        box_list = wx.BoxSizer(wx.VERTICAL)
        box_list.Add(st_names, 0, wx.ALL, 5)
        box_list.Add(self.lb_ports, 0, wx.ALL, 5)
        box_main.Add(box_list)
        # Full description.
        self.tc_detail = wx.TextCtrl(
            self, -1, size=(-1, 64),
            style=wx.TE_READONLY | wx.TE_MULTILINE
        )
        box_detail = wx.BoxSizer(wx.VERTICAL)
        box_detail.Add(self.tc_detail, 0, wx.EXPAND | wx.ALL, 5)
        box_main.Add(box_detail, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        # Controls.
        btn_ok = wx.Button(self, wx.ID_ANY, "Ok")
        btn_ok.Bind(wx.EVT_BUTTON, self.OnOk)
        btn_ok.SetBitmap(ogcIcons.Get('tick'))
        btn_cancel = wx.Button(self, wx.ID_ANY, "Cancel")
        btn_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        btn_cancel.SetBitmap(ogcIcons.Get('cross'))
        box_ctrl = wx.BoxSizer(wx.HORIZONTAL)
        box_ctrl.Add(btn_cancel, 0, wx.EXPAND)
        box_ctrl.Add(btn_ok, 0, wx.EXPAND)
        box_main.Add(box_ctrl, 0, wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        # Fit.
        self.SetSizerAndFit(box_main)
        self.Layout()
        self.lb_ports.Bind(wx.EVT_LISTBOX, self.OnSelectPort)
        self.lb_ports.SetSelection(wx.NOT_FOUND)
        self.Show(True)
        # Search for serial ports.
        ports = ogcSerialDriver.get_ports()
        port_strings = []
        self.ports = {}
        for port, desc, hwid in ports:
            port_string = f"{port}: - "
            port_string += f"'{desc}'" if desc != "n/a" else "?"
            port_string += f" - '{hwid}'" if hwid != "n/a" else ""
            port_strings.append(port_string)
            self.ports[port_string] = (port, desc, hwid)
        self.lb_ports.InsertItems(port_strings, 0)
        self.lb_ports.SetSelection(0)
        return
    
    def OnSelectPort(self, evt):
        port_string = self.lb_ports.GetStringSelection()
        port, desc, hwid = self.ports[port_string]
        self.port_name = port
        detail_string = f"Name: {port}\nDescription: {desc}\nID: {hwid}"
        self.tc_detail.SetValue(detail_string)
        self.Refresh()
        return
    
    def OnOk(self, event):
        self.Parent.Destroy()
        return
    
    def OnCancel(self, event):
        self.Parent.Destroy()
        return

################################################################################################
class ogcUploadFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Upload G-Code", size=(800,600),
                          style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        icon = wx.Icon()
        icon.CopyFromBitmap(ogcIcons.Get('page_go'))
        self.SetIcon(icon)
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.upload_panel = ogcUploadPanel(self)
        box_main.Add(self.upload_panel)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def OnClose(self):
        return

################################################################################################
