################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for the notebook panel and toolbar.
'''
################################################################################################

import wx

from .ogcIcons import ogcIcons
from .ogcEvents import ogcEvents
from .ogcPlaceHolder import ogcPlaceHolder

################################################################################################

class ogcEditorsNotebook(wx.Window):
    ICON_TERM      = 0
    ICON_PLACEHLDR = 1

    def __init__(self, parent):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditorsNotebook, self).__init__(parent, style=style)
        self.current = False
        self.Bind(ogcEvents.EVT_TAB_TITLE, self.OnTermTitle)
        self.Bind(ogcEvents.EVT_TAB_CLOSE, self.OnTermClose)
        self.Bind(ogcEvents.EVT_TAB_CURRENT, self.OnTermCurrent)
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.image_list = wx.ImageList(16, 16)
        self.image_list.Add(ogcIcons.Get('monitor'))
        self.image_list.Add(ogcIcons.Get('error'))
        self.notebook = wx.Notebook(self)
        self.notebook.SetImageList(self.image_list)
        self.tabs = []
        self.NewTab()
        box_main.Add(self.notebook, 1, wx.EXPAND)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def NewTab(self):
        self.RemovePlaceHolder()
        editor = ogcPlaceHolder(self.notebook, "TODO")
        self.tabs.append(editor)
        self.notebook.AddPage(editor, " Editor " + str(len(self.tabs)))
        self.notebook.ChangeSelection(len(self.tabs)-1)
        self.notebook.SetPageImage(len(self.tabs)-1, self.ICON_TERM)
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

    def OnTermClose(self, event):
        self.CloseTerminal(event.terminal)
        return

    def OnTermTitle(self, event):
        title = event.title
        if not len(title):
            return
        if len(title) > 24:
            title = title[:24]
        terminal = event.terminal
        for i,t in enumerate(self.tabs):
            if terminal == t:
                self.notebook.SetPageText(i, " "+title)
        return

    def OnTermCurrent(self, event):
        self.SetCurrent(True)
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
        placeholder = ogcPlaceHolder(self.notebook, "All Terminal Tabs Are Closed")
        self.tabs.append(placeholder)
        self.notebook.AddPage(placeholder, " No Terminals")
        self.notebook.SetPageImage(len(self.tabs)-1, self.ICON_PLACEHLDR)
        self.notebook.SetSelection(len(self.tabs)-1)
        return

    def IsCurrent(self):
        return self.current

    def SetCurrent(self, state):
        self.current = state
        if self.current:
            evt = ogcEvents.TabCurrent(wx.ID_ANY, notebook=self)
            wx.PostEvent(self.Parent, evt)
        return

    def GetCurrentTerm(self):
        current = self.notebook.GetSelection()
        if (current >= 0 and current < len(self.tabs) and
            not isinstance(self.tabs[current], ogcPlaceHolder)):
            return self.tabs[current]
        return None

    def SendText(self, text):
        if text is None or text == "":
            return
        current = self.GetCurrentTerm()
        current.SendText(text)
        return

################################################################################################
