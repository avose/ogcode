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
from .ogcEditorsNotebook import ogcEditorsNotebook

################################################################################################

class ogcEditorsPanel(wx.Window):
    ID_NEW         = 1001
    ID_COPY        = 1002
    ID_PASTE       = 1003
    ID_ZOOM_IN     = 1004
    ID_ZOOM_OUT    = 1005
    ID_EXIT        = 1006

    def __init__(self, parent):
        style = wx.SIMPLE_BORDER | wx.WANTS_CHARS
        super(ogcEditorsPanel, self).__init__(parent,style=style)
        self.Bind(ogcEvents.EVT_TAB_CURRENT, self.OnCurrentNotebook)
        box_main = wx.BoxSizer(wx.VERTICAL)
        self.toolbar = wx.ToolBar(self, -1, style=wx.TB_HORIZONTAL | wx.NO_BORDER)
        tools = [ (self.ID_EXIT, "Close Tab", 'cross', self.OnToolCloseTab),
                  (self.ID_NEW, "New Terminal", 'monitor_add', self.OnToolTermNew),
                  (self.ID_COPY, "Copy", 'page_copy', self.OnToolCopy),
                  (self.ID_PASTE, "Paste", 'page_paste', self.OnToolPaste),
                  (self.ID_ZOOM_OUT, "Zoom Out", 'font_delete', self.OnToolZoomOut),
                  (self.ID_ZOOM_IN, "Zoom In", 'font_add', self.OnToolZoomIn) ]
        for tool in tools:
            tid, text, icon, callback = tool
            self.toolbar.AddTool(tid, text, ogcIcons.Get(icon), wx.NullBitmap,
                                 wx.ITEM_NORMAL, text, text, None)
            self.Bind(wx.EVT_TOOL, callback, id=tid)
        self.toolbar.Realize()
        box_main.Add(self.toolbar, 0, wx.EXPAND)
        self.notebook = ogcEditorsNotebook(self)
        box_main.Add(self.notebook, 1, wx.TOP | wx.BOTTOM | wx.EXPAND, 0)
        self.SetSizerAndFit(box_main)
        self.Show(True)
        return

    def OnToolTermNew(self, event):
        self.TerminalStart()
        return

    def OnToolPaste(self, event):
        term = self.GetCurrentTerm()
        if term is not None:
            term.Paste()
        return

    def OnToolCopy(self, event):
        term = self.GetCurrentTerm()
        if term is not None:
            term.Copy()
        return

    def OnToolZoomIn(self, event):
        term = self.GetCurrentTerm()
        if term is not None:
            term.ZoomIn()
        return

    def OnToolZoomOut(self, event):
        term = self.GetCurrentTerm()
        if term is not None:
            term.ZoomOut()
        return

    def OnToolCloseTab(self, event):
        self.TerminalClose()
        return

    def OnCurrentNotebook(self, event):
        notebook = event.notebook
        for nb in self.notebooks:
            if nb != notebook:
                nb.SetCurrent(False)
        return

    def GetCurrentNotebook(self):
        for nb in self.notebooks:
            if nb.IsCurrent():
                return nb
        if len(self.notebooks):
            self.notebooks[0].SetCurrent(True)
            return self.notebooks[0]
        return None

    def GetCurrentTerm(self):
        notebook = self.GetCurrentNotebook()
        if notebook is not None:
            return notebook.GetCurrentTerm()
        return None

    def EditorLineSet(self, line):
        term = self.GetCurrentTerm()
        if term is None:
            return
        command = ogcSettings.Get('edit_line')
        command = command.replace("{LINE}",str(line))
        ogcLog.add("EditorLineSet(): "+str(line))
        term.SendText(command)
        return

    def EditorFileOpen(self, path):
        term = self.GetCurrentTerm()
        if term is None:
            return
        command = ogcSettings.Get('edit_open')
        command = command.replace("{FILE}",str(path))
        ogcLog.add("EditorFileOpen(): "+str(path))
        term.SendText(command)
        return

    def EditorStart(self, path):
        notebook = self.GetCurrentNotebook()
        if notebook is None:
            return
        term = notebook.OnNewTerm()
        command = ogcSettings.Get('edit_path') + " '%s'\x0a"%(path)
        ogcLog.add("EditorStart(): "+command)
        term.SendText(command)
        return

    def TerminalStart(self):
        notebook = self.GetCurrentNotebook()
        if notebook is None:
            return
        notebook.OnNewTerm()
        return

    def TerminalClose(self):
        notebook = self.GetCurrentNotebook()
        if notebook is None:
            return
        term = notebook.GetCurrentTerm()
        if term is not None:
            notebook.CloseTerminal(term)
        return

################################################################################################
