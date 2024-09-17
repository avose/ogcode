################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the OG-Code application entry point and main window.
'''
################################################################################################

import os
import sys
import wx

from .ogcApp import ogcApp
from .ogcHelp import ogcAboutFrame, ogcLicenseFrame
from .ogcIcons import ogcIcons
from .ogcUpload import ogcUploadFrame
from .ogcVersion import ogcVersion
from .ogcStatusBar import ogcStatusBar
from .ogcEditorsPanel import ogcEditorsPanel

from . import ogcGCode

################################################################################################
class ogcFrame(wx.Frame):
    ID_OPEN_FILE = 1000
    ID_LICENSE   = 1002
    ID_ABOUT     = 1003
    ID_SETTINGS  = 1004
    ID_UPLOAD    = 1005
    ID_EXIT      = 1006

    def __init__(self, app):
        self.app = app
        wx.Frame.__init__(self, None, wx.ID_ANY, "OC-Code - "+ogcVersion,
                          size = (1366, 768))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.icon = wx.Icon()
        self.icon.CopyFromBitmap(ogcIcons.Get('page_edit'))
        self.SetIcon(self.icon)
        self.InitUI()
        return

    def InitMenuBar(self):
        menubar = wx.MenuBar()
        # File menu.
        menu_file = wx.Menu()
        item = wx.MenuItem(menu_file, self.ID_OPEN_FILE, text="Open File")
        item.SetBitmap(ogcIcons.Get('page_add'))
        menu_file.Append(item)
        item = wx.MenuItem(menu_file, self.ID_EXIT, text="Quit")
        item.SetBitmap(ogcIcons.Get('cross'))
        menu_file.Append(item)
        menubar.Append(menu_file, 'File')
        # Laser menu.
        menu_laser = wx.Menu()
        item = wx.MenuItem(menu_laser, self.ID_UPLOAD, text="Upload G-Code")
        item.SetBitmap(ogcIcons.Get('page_go'))
        menu_laser.Append(item)
        menubar.Append(menu_laser, 'Laser')
        # Edit menu.
        menu_edit = wx.Menu()
        item = wx.MenuItem(menu_edit, self.ID_SETTINGS, text="Settings")
        item.SetBitmap(ogcIcons.Get('cog'))
        menu_edit.Append(item)
        menubar.Append(menu_edit, 'Edit')
        # Help menu.
        menu_help = wx.Menu()
        item = wx.MenuItem(menu_help, self.ID_ABOUT, text="About")
        item.SetBitmap(ogcIcons.Get('information'))
        menu_help.Append(item)
        item = wx.MenuItem(menu_help, self.ID_LICENSE, text="License")
        item.SetBitmap(ogcIcons.Get('script_key'))
        menu_help.Append(item)
        menubar.Append(menu_help, '&Help')
        # Connect menus to menu bar.
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.MenuHandler)
        self.upload_frame = None
        self.settings_frame = None
        self.about_frame = None
        self.license_frame = None
        return

    def InitStatusBar(self):
        self.statusbar = ogcStatusBar(self)
        self.SetStatusBar(self.statusbar)
        return

    def InitUI(self):
        # Setup menu bar / status bar.
        self.InitMenuBar()
        self.InitStatusBar()
        # Main box.
        box_main = wx.BoxSizer(wx.VERTICAL)
        # Add the main editors panel.
        self.editor = ogcEditorsPanel(self)
        # Finalize UI layout.
        box_main.Add(self.editor, 1, wx.TOP | wx.BOTTOM | wx.EXPAND, 0)        
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def MenuHandler(self, event):
        menu_id = event.GetId()
        if menu_id == self.ID_EXIT:
            self.OnClose()
            self.Destroy()
            return
        if menu_id == self.ID_OPEN_FILE:
            # Show file selection dialog.
            style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
            with wx.FileDialog(self, style=style) as file_dialog:
                # Do nothing if no file selected by user.
                if file_dialog.ShowModal() != wx.ID_OK:
                    return
                # Open G-code file and add to new editor tab.
                gcode_path = file_dialog.GetPath()
                try:
                    with open(gcode_path, "r") as gfile:
                        gcode = ogcGCode.gcScript(text=gfile.read())
                except Exception as excptn:
                    with wx.MessageDialog(self, "Failed to open G-code file:\n" +
                                          f"\"{gcode_path}\"\n" +
                                          f"\nError:\n{excptn}", caption="G-Code Error",
                                          style=wx.OK|wx.ICON_ERROR) as dlg:
                        dlg.ShowModal()
                    return
                self.editor.NewTab(gcode)
            return
        elif menu_id == self.ID_SETTINGS:
            if self.settings_frame is None:
                # TODO: Settings dialog.
                #self.settings_frame = ogcSettingsDialog(self)
                #self.settings_frame.Show()
                #self.settings_frame.Raise()
                pass
            else:
                self.settings_frame.Raise()
            return
        elif menu_id == self.ID_UPLOAD:
            if self.upload_frame is None:
                self.upload_frame = ogcUploadFrame(self)
            else:
                self.upload_frame.Raise()
            return
        elif menu_id == self.ID_ABOUT:
            if self.about_frame is None:
                self.about_frame = ogcAboutFrame(self)
            else:
                self.about_frame.Raise()
            return
        elif menu_id == self.ID_LICENSE:
            if self.license_frame is None:
                self.license_frame = ogcLicenseFrame(self)
            else:
                self.license_frame.Raise()
            return
        return

    def OnClose(self, event=None):
        if self.upload_frame is not None:
            self.upload_frame.OnClose()
        if self.settings_frame is not None:
            self.settings_frame.OnClose()
        if self.about_frame is not None:
            self.about_frame.OnClose()
        if self.license_frame is not None:
            self.license_frame.OnClose()
        if event is not None:
            event.Skip()
        return

    def OnDestroy(self, event):
        return

################################################################################################
def run_ogcode():
    app = ogcApp.get()
    ogcode = ogcFrame(app)
    app.SetTopWindow(ogcode)
    app.MainLoop()

################################################################################################
