################################################################################################
'''
Copyright 2025 Aaron Vose (avose@aaronvose.net)
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
        ################################
        evt, eid = wx.lib.newevent.NewCommandEvent()
        ogcEventManager.TabClose = evt
        ogcEventManager.EVT_TAB_CLOSE = eid
        ################################
        evt, eid = wx.lib.newevent.NewCommandEvent()
        ogcEventManager.TabTitle = evt
        ogcEventManager.EVT_TAB_TITLE = eid
        ################################
        evt, eid = wx.lib.newevent.NewCommandEvent()
        ogcEventManager.TabCurrent = evt
        ogcEventManager.EVT_TAB_CURRENT = eid
        ################################
        evt, eid = wx.lib.newevent.NewEvent()
        ogcEventManager.Threshold = evt
        ogcEventManager.EVT_THRESHOLD = eid
        ################################
        evt, eid = wx.lib.newevent.NewEvent()
        ogcEventManager.ShowImage = evt
        ogcEventManager.EVT_SHOW_IMAGE = eid
        ################################
        evt, eid = wx.lib.newevent.NewEvent()
        ogcEventManager.ShowLines = evt
        ogcEventManager.EVT_SHOW_LINES = eid
        ################################
        evt, eid = wx.lib.newevent.NewEvent()
        ogcEventManager.IRSize = evt
        ogcEventManager.EVT_IR_SIZE = eid
        ################################
        evt, eid = wx.lib.newevent.NewEvent()
        ogcEventManager.LaserPower = evt
        ogcEventManager.EVT_LASER_POWER = eid
        return

################################################################################################

ogcEvents = ogcEventManager()

################################################################################################
