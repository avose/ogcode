################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the geometry editors notebook.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcEditor import ogcEditorPanel
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
        self.current = False
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.image_list = wx.ImageList(16, 16)
        self.image_list.Add(ogcIcons.Get('page'))
        self.image_list.Add(ogcIcons.Get('error'))
        self.notebook = wx.Notebook(self)
        self.notebook.SetImageList(self.image_list)
        self.tabs = []
        self.AddPlaceHolder()
        box_main.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def NewTab(self, data):
        self.RemovePlaceHolder()
        if isinstance(data, wx.Image):
            editor = ogcImageEditorPanel(self.notebook, data)
            self.tabs.append(editor)
            self.notebook.AddPage(editor, " Image " + str(len(self.tabs)))
        else:
            editor = ogcEditorPanel(self.notebook, data)
            self.tabs.append(editor)
            self.notebook.AddPage(editor, " Geometry " + str(len(self.tabs)))
        self.notebook.ChangeSelection(len(self.tabs)-1)
        self.notebook.SetPageImage(len(self.tabs)-1, self.ICON_EDITOR)
        return editor

    def CloseEditor(self, editor):
        if editor is None:
            return
        for i,t in enumerate(self.tabs):
            if editor == t:
                self.notebook.DeletePage(i)
                self.notebook.SendSizeEvent()
                self.tabs.remove(self.tabs[i])
        self.AddPlaceHolder()
        return

    def RemovePlaceHolder(self):
        if len(self.tabs) != 1 or not isinstance(self.tabs[0], ogcPlaceHolder):
            return
        self.notebook.DeletePage(0)
        self.notebook.SendSizeEvent()
        self.tabs.remove(self.tabs[0])
        return

    def AddPlaceHolder(self):
        if len(self.tabs):
            return
        placeholder = ogcPlaceHolder(self.notebook, self.min_size, "All Files Are Closed.")
        self.tabs.append(placeholder)
        self.notebook.AddPage(placeholder, " No Open Files.")
        self.notebook.SetPageImage(len(self.tabs)-1, self.ICON_PLACEHLDR)
        self.notebook.SetSelection(len(self.tabs)-1)
        return

################################################################################################
