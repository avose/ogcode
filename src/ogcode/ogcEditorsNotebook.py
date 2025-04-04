################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the geometry editors notebook.
'''
################################################################################################

import wx
import os

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcImageEditor import ogcImageEditorPanel
from .ogcPlaceHolder import ogcPlaceHolder

################################################################################################

class ogcEditorsNotebook(wx.Window):
    ICON_EDITOR    = 0
    ICON_PLACEHLDR = 1

    def __init__(self, parent):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditorsNotebook, self).__init__(parent, style=style)
        self.min_size = [640, 480]
        self.SetMinSize(self.min_size)
        self.current = False
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.image_list = wx.ImageList(16, 16)
        self.image_list.Add(ogcIcons.Get('page'))
        self.image_list.Add(ogcIcons.Get('error'))
        self.notebook = wx.Notebook(self)
        self.notebook.SetMinSize(self.min_size)
        self.notebook.SetImageList(self.image_list)
        self.tabs = []
        self.AddPlaceHolder()
        box_main.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def NewTab(self, data, path):
        # Remove placeholder and add a new tab.
        self.RemovePlaceHolder()
        editor = ogcImageEditorPanel(self.notebook, data, path)
        self.tabs.append(editor)
        self.notebook.AddPage(editor, f" {os.path.basename(path)}")
        self.notebook.ChangeSelection(len(self.tabs)-1)
        self.notebook.SetPageImage(len(self.tabs)-1, self.ICON_EDITOR)
        return editor

    def CurrentTab(self):
        # Return the current tab as an object.
        return self.tabs[self.notebook.GetSelection()]

    def CloseTab(self, tab = None):
        # Close current tab and add a placeholder tab if needed.
        tab = self.CurrentTab() if tab is None else tab
        for i,t in enumerate(self.tabs):
            if tab == t:
                self.notebook.DeletePage(i)
                self.notebook.SendSizeEvent()
                self.tabs.remove(self.tabs[i])
        self.AddPlaceHolder()
        return

    def RemovePlaceHolder(self):
        # Remove placeholder tab if there is one.
        if len(self.tabs) != 1 or not isinstance(self.tabs[0], ogcPlaceHolder):
            return
        self.notebook.DeletePage(0)
        self.notebook.SendSizeEvent()
        self.tabs.remove(self.tabs[0])
        return

    def AddPlaceHolder(self):
        # Add placeholder tab if needed.
        if len(self.tabs):
            return
        placeholder = ogcPlaceHolder(self.notebook, self.min_size, "All Files Are Closed.")
        self.tabs.append(placeholder)
        self.notebook.AddPage(placeholder, " No Open Files.")
        self.notebook.SetPageImage(len(self.tabs)-1, self.ICON_PLACEHLDR)
        self.notebook.SetSelection(len(self.tabs)-1)
        return

################################################################################################
