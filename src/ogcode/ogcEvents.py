################################################################################################
'''
Copyright 2024 Aaron Vose (avose@aaronvose.net)
Licensed under the LGPL v2.1; see the file 'LICENSE' for details.

This file holds the code for custom application events.
'''
################################################################################################

import wx
import wx.lib.newevent

################################################################################################
class ogcEventManager():
    initialized = False

    def __init__(self):
        if ogcEventManager.initialized:
            return
        ogcEventManager.initialized = True
        evt, eid = wx.lib.newevent.NewCommandEvent()
        ogcEventManager.TabClose = evt
        ogcEventManager.EVT_TAB_CLOSE = eid
        evt, eid = wx.lib.newevent.NewCommandEvent()
        ogcEventManager.TabTitle = evt
        ogcEventManager.EVT_TAB_TITLE = eid
        evt, eid = wx.lib.newevent.NewCommandEvent()
        ogcEventManager.TabCurrent = evt
        ogcEventManager.EVT_TAB_CURRENT = eid
        return

################################################################################################

ogcEvents = ogcEventManager()

################################################################################################
