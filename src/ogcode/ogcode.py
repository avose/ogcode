################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the OG-Code application entry point and main window.
'''
################################################################################################

import os
import sys
import wx

from .ogcApp import ogcApp
from .ogcLog import ogcLog
from .ogcHelp import ogcAboutFrame, ogcLicenseFrame, ogcDonateFrame
from .ogcIcons import ogcIcons
from .ogcVersion import ogcVersion
from .ogcEngrave import ogcEngraveFrame
from .ogcStatusBar import ogcStatusBar
from .ogcEditorsPanel import ogcEditorsPanel

from . import ogcGCode

################################################################################################
class ogcFrame(wx.Frame):
    ID_OPEN_FILE = wx.NewIdRef()
    ID_SAVE_FILE = wx.NewIdRef()
    ID_LICENSE   = wx.NewIdRef()
    ID_ABOUT     = wx.NewIdRef()
    ID_DONATE    = wx.NewIdRef()
    ID_SETTINGS  = wx.NewIdRef()
    ID_ENGRAVE   = wx.NewIdRef()
    ID_EXIT      = wx.NewIdRef()

    ################################################################
    def __init__(self, app):
        self.app = app
        wx.Frame.__init__(self, None, wx.ID_ANY, f"OG-Code - {ogcVersion}",
                          size = (1366, 768))
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.icon = wx.Icon()
        self.icon.CopyFromBitmap(ogcIcons.Get('chart_line'))
        self.SetIcon(self.icon)
        self.InitUI()
        return

    ################################################################
    def InitMenuBar(self):
        menubar = wx.MenuBar()
        # File menu.
        menu_file = wx.Menu()
        item = wx.MenuItem(menu_file, self.ID_OPEN_FILE, text="Open File")
        item.SetBitmap(ogcIcons.Get('page_add'))
        menu_file.Append(item)
        item = wx.MenuItem(menu_file, self.ID_SAVE_FILE, text="Save File")
        item.SetBitmap(ogcIcons.Get('disk'))
        menu_file.Append(item)
        item = wx.MenuItem(menu_file, self.ID_EXIT, text="Quit")
        item.SetBitmap(ogcIcons.Get('cross'))
        menu_file.Append(item)
        menubar.Append(menu_file, 'File')
        # Laser menu.
        menu_laser = wx.Menu()
        item = wx.MenuItem(menu_laser, self.ID_ENGRAVE, text="Engrave")
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
        item = wx.MenuItem(menu_help, self.ID_DONATE, text="Donate")
        item.SetBitmap(ogcIcons.Get('money_dollar'))
        menu_help.Append(item)
        menubar.Append(menu_help, '&Help')
        # Connect menus to menu bar.
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.MenuHandler)
        self.engrave_frame = None
        self.settings_frame = None
        self.about_frame = None
        self.license_frame = None
        self.donate_frame = None
        return

    ################################################################
    def InitStatusBar(self):
        self.statusbar = ogcStatusBar(self)
        self.SetStatusBar(self.statusbar)
        return

    ################################################################
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

    ################################################################
    def OpenFileDialog(self):
        # Open a file dialog and return loaded image or gcode data.
        # Show file selection dialog.
        style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        with wx.FileDialog(self, style=style) as file_dialog:
            # Do nothing if no file selected by user.
            if file_dialog.ShowModal() != wx.ID_OK:
                return (None, None)
            # Check if the file is an image file else assume G-code.
            file_path = os.path.abspath(file_dialog.GetPath())
            if wx.Image.CanRead(file_path):
                # Open as image.
                image = wx.Image(file_path, wx.BITMAP_TYPE_ANY)
                ogcLog.add(f"Opened Image from: '{file_path}'")
                return (image, file_path)
            else:
                # Open as G-Code.
                try:
                    with open(file_path, "r") as gfile:
                        gcode = ogcGCode.gcScript(text=gfile.read())
                    ogcLog.add(f"Opened G-Code from: '{file_path}'")
                    return (gcode, file_path)
                except Exception as excptn:
                    with wx.MessageDialog(self, "Failed to open G-code file:\n" +
                                          f"\"{file_path}\"\n" +
                                          f"\nError:\n{excptn}", caption="G-Code Error",
                                          style=wx.OK|wx.ICON_ERROR) as dlg:
                        dlg.ShowModal()
                    return (None, None)
        return (None, None)

    ################################################################
    def SaveFileDialog(self, gcode):
        # Open a save file dialog for storing G-Code.
        style = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        wildcard = "G-Code files (*.ngc)|*.ngc"
        with wx.FileDialog(self, message="Save G-Code file", wildcard=wildcard,
                           style=style) as file_dialog:
            # Do nothing if no file selected by user.
            if file_dialog.ShowModal() != wx.ID_OK:
                return None
            file_path = os.path.abspath(file_dialog.GetPath())
            # Ensure the file has the .ngc extension.
            if not file_path.lower().endswith(".ngc"):
                file_path += ".ngc"
            # Write G-Code to the file.
            with open(file_path, "w", encoding="utf-8") as gcode_file:
                gcode_file.write(gcode)
                gcode_file.write("\n")
            ogcLog.add(f"Wrote G-Code to: '{file_path}'")
        return

    ################################################################
    def OpenEngraveDialog(self):
        # Open engrave dialog.
        if self.engrave_frame is None:
            tab = self.editor.CurrentTab()
            gcode = self.editor.CurrentTab().GetGCode()
            if gcode is None:
                return
            self.engrave_frame = ogcEngraveFrame(self, gcode)
        else:
            self.engrave_frame.Raise()
        return

    ################################################################
    def MenuHandler(self, event):
        menu_id = event.GetId()
        if menu_id == self.ID_EXIT:
            # Quit Application.
            self.OnClose()
            self.Destroy()
            return
        elif menu_id == self.ID_OPEN_FILE:
            # Open a new file.
            data, file_path = self.OpenFileDialog()
            if data is not None and file_path is not None:
                self.editor.NewTab(data, file_path)
            return
        elif menu_id == self.ID_SAVE_FILE:
            # Open a new file.
            tab = self.editor.CurrentTab()
            gcode = self.editor.CurrentTab().GetGCode()
            if gcode is not None:
                self.SaveFileDialog(gcode)
            return
        elif menu_id == self.ID_SETTINGS:
            # Open settings dialog.
            if self.settings_frame is None:
                # TODO: Settings dialog.
                #self.settings_frame = ogcSettingsDialog(self)
                #self.settings_frame.Show()
                #self.settings_frame.Raise()
                pass
            else:
                self.settings_frame.Raise()
            return
        elif menu_id == self.ID_ENGRAVE:
            # Open engrave dialog.
            self.OpenEngraveDialog()
            return
        elif menu_id == self.ID_ABOUT:
            # Open about dialog.
            if self.about_frame is None:
                self.about_frame = ogcAboutFrame(self)
            else:
                self.about_frame.Raise()
            return
        elif menu_id == self.ID_LICENSE:
            # Open license dialog.
            if self.license_frame is None:
                self.license_frame = ogcLicenseFrame(self)
            else:
                self.license_frame.Raise()
            return
        elif menu_id == self.ID_DONATE:
            # Open donation dialog.
            if self.donate_frame is None:
                self.donate_frame = ogcDonateFrame(self)
            else:
                self.donate_frame.Raise()
            return
        return

    ################################################################
    def OnClose(self, event=None):
        # Close any open dialogs.
        if self.engrave_frame is not None:
            self.engrave_frame.OnClose()
            self.engrave_frame = None
        if self.settings_frame is not None:
            self.settings_frame.OnClose()
            self.settings_frame = None
        if self.about_frame is not None:
            self.about_frame.OnClose()
            self.about_frame = None
        if self.license_frame is not None:
            self.license_frame.OnClose()
            self.license_frame = None
        # Skip the event so it is propagated to other event handlers.
        if event is not None:
            event.Skip()
        return

    ################################################################
    def OnDestroy(self, event):
        event.Skip()
        return

################################################################################################
def run_ogcode():
    app = ogcApp.get()
    ogcode = ogcFrame(app)
    app.SetTopWindow(ogcode)
    app.MainLoop()

################################################################################################
